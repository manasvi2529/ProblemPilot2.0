"""
Search Dispatcher — Multi-Provider Orchestration, Quota Failover, and URL Deduplication.
"""
import asyncio
import logging
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from backend.config import settings
from backend.services.search_providers.base import (
    BaseSearchAdapter,
    SearchResult,
    SearchBatch,
    SearchQuotaExhaustedError,
    SearchAuthError,
    SearchTransientError,
    SearchProviderError,
)
from backend.services.search_providers.serper import SerperAdapter
from backend.services.search_providers.brave import BraveAdapter
from backend.services.search_providers.google_custom import GoogleCustomAdapter

logger = logging.getLogger(__name__)


def canonicalize_url(url: str) -> str:
    """Normalize URL by stripping tracking parameters, fragments, and standardizing casing."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        # Parse query params and strip tracking tokens
        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_params = [
            (k, v) for k, v in query_params
            if not k.lower().startswith("utm_")
            and k.lower() not in ("ref", "source", "fbclid", "gclid", "mc_eid")
        ]
        cleaned_query = urllib.parse.urlencode(cleaned_params)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        canonical = urllib.parse.urlunparse((
            parsed.scheme.lower() or "https",
            netloc,
            path,
            "",  # params
            cleaned_query,
            "",  # fragment stripped
        ))
        return canonical
    except Exception:
        return url.strip()


@dataclass
class SearchDispatchResult:
    """Consolidated result returned by SearchDispatcher."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_mode: str  # "live" | "mixed" | "curated_fallback"
    providers_attempted: List[str]
    providers_diagnostics: Dict[str, Any]
    failover_occurred: bool
    total_duration_ms: float
    error_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total_results": self.total_results,
            "search_mode": self.search_mode,
            "providers_attempted": self.providers_attempted,
            "providers_diagnostics": self.providers_diagnostics,
            "failover_occurred": self.failover_occurred,
            "total_duration_ms": self.total_duration_ms,
            "error_summary": self.error_summary,
        }


class SearchDispatcher:
    """
    Orchestrates search requests across Serper, Brave, and legacy Google providers.
    Handles backoff, Retry-After delays, quota exhaustion failovers, and canonical deduplication.
    """

    def __init__(self, adapters: Optional[List[BaseSearchAdapter]] = None):
        if adapters:
            self.adapters = adapters
        else:
            self.adapters = self._build_configured_adapters()

    def _build_configured_adapters(self) -> List[BaseSearchAdapter]:
        """Build ordered list of provider adapters based on environment configuration."""
        configured_mode = settings.SEARCH_PROVIDER.lower()
        serper = SerperAdapter()
        brave = BraveAdapter()
        google = GoogleCustomAdapter()

        if configured_mode == "serper":
            return [serper, brave, google]
        elif configured_mode == "brave":
            return [brave, serper, google]
        elif configured_mode == "google_custom":
            return [google, serper, brave]
        else:
            # "auto" or default priority: Serper (Google proxy) -> Brave (independent) -> GoogleCustom (legacy)
            return [serper, brave, google]

    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Deduplicate search results using canonical URL normalization, retaining highest score."""
        seen: Dict[str, SearchResult] = {}
        for r in results:
            canon = canonicalize_url(r.url)
            if not canon:
                continue
            if canon not in seen:
                seen[canon] = r
            else:
                if r.relevance_score > seen[canon].relevance_score:
                    seen[canon] = r
        return list(seen.values())

    async def search(
        self,
        query: str,
        num_results: int = 10,
        max_retries_per_provider: int = 2,
        initial_backoff_sec: float = 0.5,
    ) -> SearchDispatchResult:
        """
        Executes search with automatic failover, backoff, and truthful diagnostics.
        If no provider succeeds or no credentials are configured, returns curated_fallback mode.
        """
        start_time = time.time()
        providers_attempted: List[str] = []
        providers_diagnostics: Dict[str, Any] = {}
        failover_occurred = False
        all_results: List[SearchResult] = []

        # Find providers that are configured with keys
        available_adapters = [a for a in self.adapters if a.is_configured]

        if not available_adapters:
            # Transparent fallback: no search credentials configured
            duration_ms = (time.time() - start_time) * 1000.0
            return SearchDispatchResult(
                query=query,
                results=[],
                total_results=0,
                search_mode="curated_fallback",
                providers_attempted=[],
                providers_diagnostics={"fallback_reason": "No search provider credentials configured in environment"},
                failover_occurred=False,
                total_duration_ms=round(duration_ms, 2),
                error_summary="No search credentials configured",
            )

        last_error = None

        for adapter_idx, adapter in enumerate(available_adapters):
            provider_name = adapter.provider_name
            providers_attempted.append(provider_name)
            if adapter_idx > 0:
                failover_occurred = True

            logger.info("Executing search query '%s' on provider '%s'", query, provider_name)
            success = False

            for attempt in range(max_retries_per_provider + 1):
                try:
                    batch = await adapter.search(query=query, num_results=num_results)
                    all_results.extend(batch.results)
                    providers_diagnostics[provider_name] = {
                        "status": "success",
                        "results_count": len(batch.results),
                        "duration_ms": batch.duration_ms,
                        "attempts": attempt + 1,
                    }
                    success = True
                    break
                except SearchQuotaExhaustedError as exc:
                    logger.warning("Provider '%s' quota exhausted: %s. Initiating failover.", provider_name, exc)
                    providers_diagnostics[provider_name] = {
                        "status": "quota_exhausted",
                        "error": exc.message,
                        "status_code": exc.status_code,
                        "attempts": attempt + 1,
                    }
                    last_error = exc
                    # Do not retry quota exhausted; immediately failover to next provider
                    break
                except SearchAuthError as exc:
                    logger.error("Provider '%s' authentication failed: %s. Initiating failover.", provider_name, exc)
                    providers_diagnostics[provider_name] = {
                        "status": "auth_error",
                        "error": exc.message,
                        "status_code": exc.status_code,
                        "attempts": attempt + 1,
                    }
                    last_error = exc
                    # Do not retry invalid authentication
                    break
                except SearchTransientError as exc:
                    last_error = exc
                    if attempt < max_retries_per_provider:
                        backoff = initial_backoff_sec * (2 ** attempt)
                        logger.info("Transient error on '%s': %s. Retrying in %.2fs (attempt %d/%d)",
                                    provider_name, exc, backoff, attempt + 1, max_retries_per_provider)
                        await asyncio.sleep(backoff)
                    else:
                        providers_diagnostics[provider_name] = {
                            "status": "transient_failure",
                            "error": exc.message,
                            "status_code": exc.status_code,
                            "attempts": attempt + 1,
                        }
                except Exception as exc:
                    last_error = exc
                    providers_diagnostics[provider_name] = {
                        "status": "error",
                        "error": str(exc),
                        "attempts": attempt + 1,
                    }
                    break

            if success and all_results:
                # Successfully got results from this provider
                break

        duration_ms = (time.time() - start_time) * 1000.0
        deduped = self.deduplicate_results(all_results)

        # Truthful Search Mode Determination
        if deduped:
            search_mode = "live"
        else:
            search_mode = "curated_fallback"

        return SearchDispatchResult(
            query=query,
            results=deduped,
            total_results=len(deduped),
            search_mode=search_mode,
            providers_attempted=providers_attempted,
            providers_diagnostics=providers_diagnostics,
            failover_occurred=failover_occurred,
            total_duration_ms=round(duration_ms, 2),
            error_summary=str(last_error) if last_error else None,
        )

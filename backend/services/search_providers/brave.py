"""
Brave Search Provider Adapter (Secondary Recommended Provider).
"""
import time
import urllib.parse
from typing import Optional, List
import httpx
from backend.config import settings
from backend.services.search_providers.base import (
    BaseSearchAdapter,
    SearchResult,
    SearchBatch,
    ProviderHealth,
    SearchAuthError,
    SearchQuotaExhaustedError,
    SearchTransientError,
    SearchProviderError,
)


class BraveAdapter(BaseSearchAdapter):
    """Adapter for Brave Search Web Search API."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.effective_brave_key
        self._endpoint = "https://api.search.brave.com/res/v1/web/search"

    @property
    def provider_name(self) -> str:
        return "brave"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key not in ("your-brave-api-key-here", ""))

    async def search(self, query: str, num_results: int = 10, **kwargs) -> SearchBatch:
        if not self.is_configured:
            raise SearchAuthError("Brave Search API key is not configured", provider=self.provider_name)

        start_time = time.time()
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key,
            "User-Agent": "Problem2Project-AI/1.7",
        }
        params = {
            "q": query,
            "count": min(max(num_results, 1), 20),
            "text_decorations": "false",
            "search_lang": "en",
        }

        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            try:
                response = await client.get(self._endpoint, headers=headers, params=params)
            except httpx.TimeoutException as exc:
                raise SearchTransientError(f"Brave API request timed out: {exc}", provider=self.provider_name) from exc
            except httpx.RequestError as exc:
                raise SearchTransientError(f"Brave network error: {exc}", provider=self.provider_name) from exc

        status = response.status_code
        if status in (401, 403):
            raise SearchAuthError(
                f"Brave authentication failed (HTTP {status}): Check BRAVE_SEARCH_API_KEY",
                provider=self.provider_name,
                status_code=status,
            )
        elif status == 429:
            raise SearchQuotaExhaustedError(
                "Brave quota or rate limit exhausted (HTTP 429)",
                provider=self.provider_name,
                status_code=status,
            )
        elif status >= 500:
            raise SearchTransientError(
                f"Brave upstream server error (HTTP {status})",
                provider=self.provider_name,
                status_code=status,
            )
        elif status != 200:
            raise SearchProviderError(
                f"Brave unexpected HTTP error: {status}",
                provider=self.provider_name,
                status_code=status,
            )

        data = response.json()
        duration_ms = (time.time() - start_time) * 1000.0

        web_results = data.get("web", {}).get("results", [])
        results: List[SearchResult] = []

        for idx, item in enumerate(web_results):
            url = item.get("url", "")
            if not url:
                continue

            publisher = item.get("profile", {}).get("name")
            if not publisher:
                try:
                    domain = urllib.parse.urlparse(url).netloc
                    if domain:
                        publisher = domain.lower().replace("www.", "")
                except Exception:
                    publisher = None

            result = SearchResult(
                url=url,
                title=item.get("title", ""),
                snippet=item.get("description", ""),
                publisher=publisher,
                publication_date=item.get("age"),
                relevance_score=max(0.1, 1.0 - (idx * 0.05)),
                provider=self.provider_name,
                raw_data=item,
            )
            results.append(result)

        return SearchBatch(
            query=query,
            results=results,
            total_results=len(results),
            provider=self.provider_name,
            search_mode="live",
            duration_ms=round(duration_ms, 2),
            metadata={"query_term": query},
        )

    async def check_health(self) -> ProviderHealth:
        if not self.is_configured:
            return ProviderHealth(
                provider=self.provider_name,
                is_healthy=False,
                error_message="BRAVE_SEARCH_API_KEY is not configured",
            )
        try:
            batch = await self.search(query="test probe", num_results=1)
            return ProviderHealth(
                provider=self.provider_name,
                is_healthy=True,
                status_code=200,
            )
        except SearchProviderError as exc:
            return ProviderHealth(
                provider=self.provider_name,
                is_healthy=False,
                error_message=exc.message,
                status_code=exc.status_code,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.provider_name,
                is_healthy=False,
                error_message=str(exc),
            )

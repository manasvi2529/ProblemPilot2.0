"""
Serper.dev Search Provider Adapter (Primary Recommended Provider).
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


class SerperAdapter(BaseSearchAdapter):
    """Adapter for Serper.dev Google Organic Search API."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.effective_serper_key
        self._endpoint = "https://google.serper.dev/search"

    @property
    def provider_name(self) -> str:
        return "serper"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key not in ("your-serper-api-key-here", ""))

    async def search(self, query: str, num_results: int = 10, **kwargs) -> SearchBatch:
        if not self.is_configured:
            raise SearchAuthError("Serper API key is not configured", provider=self.provider_name)

        start_time = time.time()
        headers = {
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
            "User-Agent": "Problem2Project-AI/1.7",
        }
        payload = {
            "q": query,
            "num": min(max(num_results, 1), 20),
        }

        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            try:
                response = await client.post(self._endpoint, headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                raise SearchTransientError(f"Serper API request timed out: {exc}", provider=self.provider_name) from exc
            except httpx.RequestError as exc:
                raise SearchTransientError(f"Serper network error: {exc}", provider=self.provider_name) from exc

        status = response.status_code
        if status in (401, 403):
            raise SearchAuthError(
                f"Serper authentication failed (HTTP {status}): Check SERPER_API_KEY",
                provider=self.provider_name,
                status_code=status,
            )
        elif status == 429:
            raise SearchQuotaExhaustedError(
                "Serper quota exhausted (HTTP 429)",
                provider=self.provider_name,
                status_code=status,
            )
        elif status >= 500:
            raise SearchTransientError(
                f"Serper upstream server error (HTTP {status})",
                provider=self.provider_name,
                status_code=status,
            )
        elif status != 200:
            raise SearchProviderError(
                f"Serper unexpected HTTP error: {status}",
                provider=self.provider_name,
                status_code=status,
            )

        data = response.json()
        duration_ms = (time.time() - start_time) * 1000.0

        organic = data.get("organic", [])
        results: List[SearchResult] = []

        for idx, item in enumerate(organic):
            url = item.get("link", "")
            if not url:
                continue

            # Extract publisher from domain or snippet if present; do not fabricate
            publisher = None
            try:
                domain = urllib.parse.urlparse(url).netloc
                if domain:
                    publisher = domain.lower().replace("www.", "")
            except Exception:
                pass

            result = SearchResult(
                url=url,
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                publisher=publisher,
                publication_date=item.get("date"),
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
            metadata={"credits": data.get("credits", 1)},
        )

    async def check_health(self) -> ProviderHealth:
        if not self.is_configured:
            return ProviderHealth(
                provider=self.provider_name,
                is_healthy=False,
                error_message="SERPER_API_KEY is not configured",
            )
        try:
            # Query a minimal test probe
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

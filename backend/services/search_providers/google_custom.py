"""
Google Custom Search API Adapter (Optional Legacy Provider).
Note: Google Custom Search JSON API is closed to new customers and scheduled
for deprecation transition by January 1, 2027. Retained for backward compatibility.
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


class GoogleCustomAdapter(BaseSearchAdapter):
    """Adapter for Google Custom Search JSON API (Legacy)."""

    def __init__(self, api_key: Optional[str] = None, engine_id: Optional[str] = None):
        self._api_key = api_key or settings.effective_google_search_key
        self._engine_id = engine_id or settings.effective_google_search_engine_id
        self._endpoint = "https://www.googleapis.com/customsearch/v1"

    @property
    def provider_name(self) -> str:
        return "google_custom"

    @property
    def is_configured(self) -> bool:
        return bool(
            self._api_key
            and self._api_key not in ("your-search-api-key-here", "")
            and self._engine_id
            and self._engine_id not in ("your-search-engine-id-here", "")
        )

    async def search(self, query: str, num_results: int = 10, **kwargs) -> SearchBatch:
        if not self.is_configured:
            raise SearchAuthError("Google Custom Search credentials not configured", provider=self.provider_name)

        start_time = time.time()
        params = {
            "key": self._api_key,
            "cx": self._engine_id,
            "q": query,
            "num": min(max(num_results, 1), 10),  # Google API max per request is 10
        }

        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            try:
                response = await client.get(self._endpoint, params=params)
            except httpx.TimeoutException as exc:
                raise SearchTransientError(f"Google Custom Search timed out: {exc}", provider=self.provider_name) from exc
            except httpx.RequestError as exc:
                raise SearchTransientError(f"Google network error: {exc}", provider=self.provider_name) from exc

        status = response.status_code
        if status != 200:
            error_body = {}
            try:
                error_body = response.json().get("error", {})
            except Exception:
                pass
            message = error_body.get("message", f"HTTP {status}")
            errors = error_body.get("errors", [])
            reasons = [e.get("reason", "") for e in errors]

            if "dailyLimitExceeded" in reasons or "quotaExceeded" in reasons or status == 429:
                raise SearchQuotaExhaustedError(
                    f"Google Custom Search quota exhausted: {message}",
                    provider=self.provider_name,
                    status_code=status,
                )
            elif status in (400, 401, 403):
                raise SearchAuthError(
                    f"Google Custom Search auth/key error: {message}",
                    provider=self.provider_name,
                    status_code=status,
                )
            elif status >= 500:
                raise SearchTransientError(
                    f"Google server error: {status}",
                    provider=self.provider_name,
                    status_code=status,
                )
            else:
                raise SearchProviderError(
                    f"Google Search error: {message}",
                    provider=self.provider_name,
                    status_code=status,
                )

        data = response.json()
        duration_ms = (time.time() - start_time) * 1000.0

        items = data.get("items", [])
        results: List[SearchResult] = []

        for idx, item in enumerate(items):
            url = item.get("link", "")
            if not url:
                continue

            publisher = item.get("displayLink")
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
                snippet=item.get("snippet", ""),
                publisher=publisher,
                publication_date=None,
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
            metadata={"searchInformation": data.get("searchInformation", {})},
        )

    async def check_health(self) -> ProviderHealth:
        if not self.is_configured:
            return ProviderHealth(
                provider=self.provider_name,
                is_healthy=False,
                error_message="Google Custom Search API key or Engine ID is not configured",
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

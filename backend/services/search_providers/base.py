"""
Base interfaces and data structures for external search providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


class SearchProviderError(Exception):
    """Base exception for search provider operations."""
    def __init__(self, message: str, provider: str = "unknown", status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code


class SearchAuthError(SearchProviderError):
    """Raised on 401/403 invalid API key or permission failure (non-retriable)."""
    pass


class SearchQuotaExhaustedError(SearchProviderError):
    """Raised on 429 quota exhaustion or daily limit reached (triggers failover)."""
    pass


class SearchTransientError(SearchProviderError):
    """Raised on network timeout, 502/503/504 errors (retriable with backoff)."""
    pass


class SSRFSecurityError(SearchProviderError):
    """Raised when URL or resolved IP violates SSRF security boundaries."""
    pass


@dataclass
class SearchResult:
    """Standardized search result representation across all search providers."""
    url: str
    title: str
    snippet: str
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    relevance_score: float = 0.0
    provider: str = ""
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "publisher": self.publisher,
            "publication_date": self.publication_date,
            "relevance_score": self.relevance_score,
            "provider": self.provider,
        }


@dataclass
class SearchBatch:
    """Standardized batch response from a search provider query."""
    query: str
    results: List[SearchResult]
    total_results: int
    provider: str
    search_mode: str = "live"  # "live" | "curated_fallback"
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total_results": self.total_results,
            "provider": self.provider,
            "search_mode": self.search_mode,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class ProviderHealth:
    """Diagnostic health check result for a search provider."""
    provider: str
    is_healthy: bool
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "is_healthy": self.is_healthy,
            "error_message": self.error_message,
            "status_code": self.status_code,
            "last_checked": self.last_checked.isoformat(),
        }


class BaseSearchAdapter(ABC):
    """Abstract base class for all search provider adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'serper', 'brave', 'google_custom')."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the provider has necessary API credentials configured."""
        pass

    @abstractmethod
    async def search(self, query: str, num_results: int = 10, **kwargs) -> SearchBatch:
        """Execute web search and return standardized SearchBatch."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Verify credential validity and connectivity."""
        pass

"""
Search providers package — modular search adapters and security guards.
"""
from backend.services.search_providers.base import (
    BaseSearchAdapter,
    SearchResult,
    SearchBatch,
    ProviderHealth,
    SearchProviderError,
    SearchAuthError,
    SearchQuotaExhaustedError,
    SearchTransientError,
    SSRFSecurityError,
)
from backend.services.search_providers.ssrf_guard import (
    safe_fetch_page_content,
    resolve_and_validate_hostname,
    validate_ip_address,
    is_ip_prohibited,
    ExtractedPage,
    SafePinnedTransport,
)
from backend.services.search_providers.serper import SerperAdapter
from backend.services.search_providers.brave import BraveAdapter
from backend.services.search_providers.google_custom import GoogleCustomAdapter
from backend.services.search_providers.dispatcher import SearchDispatcher, SearchDispatchResult, canonicalize_url

__all__ = [
    "BaseSearchAdapter",
    "SearchResult",
    "SearchBatch",
    "ProviderHealth",
    "SearchProviderError",
    "SearchAuthError",
    "SearchQuotaExhaustedError",
    "SearchTransientError",
    "SSRFSecurityError",
    "safe_fetch_page_content",
    "resolve_and_validate_hostname",
    "validate_ip_address",
    "is_ip_prohibited",
    "ExtractedPage",
    "SafePinnedTransport",
    "SerperAdapter",
    "BraveAdapter",
    "GoogleCustomAdapter",
    "SearchDispatcher",
    "SearchDispatchResult",
    "canonicalize_url",
]

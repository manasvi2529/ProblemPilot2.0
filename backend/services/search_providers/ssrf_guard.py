"""
Hardened SSRF Guard, Anti-Rebinding Connection Pinning, and Safe Content Extractor.
"""
import ipaddress
import logging
import socket
import ssl
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional, Tuple
import bs4
import httpx
import httpcore
import httpcore._backends.auto as auto
from backend.services.search_providers.base import SSRFSecurityError

logger = logging.getLogger(__name__)

# Strict prohibited IP networks (IPv4 & IPv6)
PROHIBITED_NETWORKS = [
    # IPv4 Private / Loopback / Link-Local / Reserved / Metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),       # CGNAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-Local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),      # Private RFC 1918
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),     # Private RFC 1918
    ipaddress.ip_network("198.18.0.0/15"),      # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    # IPv6 Loopback / Private / Link-Local / Multicast / IPv4-mapped
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-mapped IPv6
    ipaddress.ip_network("100::/64"),           # Discard prefix
    ipaddress.ip_network("64:ff9b::/96"),       # IPv4/IPv6 translation
    ipaddress.ip_network("2001:db8::/32"),      # Documentation
    ipaddress.ip_network("fc00::/7"),           # Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),          # Link-Local
    ipaddress.ip_network("ff00::/8"),           # Multicast
]


def is_ip_prohibited(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to any prohibited private, loopback, or cloud network."""
    # Check IPv4-mapped IPv6 explicitly
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_reserved
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
    ):
        return True

    for net in PROHIBITED_NETWORKS:
        if ip in net:
            return True

    return False


def validate_ip_address(ip_str: str) -> None:
    """Validate a single IP string; raises SSRFSecurityError if prohibited."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError as exc:
        raise SSRFSecurityError(f"Invalid IP address format: {ip_str}") from exc

    if is_ip_prohibited(ip_obj):
        raise SSRFSecurityError(f"Access to prohibited/private IP '{ip_str}' is denied")


def resolve_and_validate_hostname(hostname: str, port: int = 443) -> List[str]:
    """
    Resolve all A (IPv4) and AAAA (IPv6) records for hostname.
    If ANY returned address is prohibited, rejects the host.
    Returns list of validated IP strings.
    """
    # Check if hostname is an IP literal
    try:
        ip_obj = ipaddress.ip_address(hostname.strip("[]"))
        if is_ip_prohibited(ip_obj):
            raise SSRFSecurityError(f"Access to prohibited/private IP literal '{hostname}' is denied")
        return [str(ip_obj)]
    except ValueError:
        pass  # Not an IP literal, proceed to DNS resolution

    try:
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SSRFSecurityError(f"DNS resolution failed for host '{hostname}': {exc}") from exc

    resolved_ips: List[str] = []
    for family, socktype, proto, canonname, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if is_ip_prohibited(ip_obj):
            raise SSRFSecurityError(
                f"SSRF Security Violation: Host '{hostname}' resolved to prohibited IP '{ip_str}'"
            )
        if ip_str not in resolved_ips:
            resolved_ips.append(ip_str)

    if not resolved_ips:
        raise SSRFSecurityError(f"No valid IP addresses resolved for host '{hostname}'")

    return resolved_ips


class PinnedBackend(auto.AutoBackend):
    """
    Custom httpcore network backend that forces connection to a pre-validated IP
    while allowing TLS handshake to use the original request hostname (SNI + cert verification).
    """
    def __init__(self, pinned_ip: str):
        super().__init__()
        self.pinned_ip = pinned_ip

    async def connect_tcp(self, host: str, port: int, timeout: float | None = None, local_address: str | None = None, socket_options = None):
        # Route socket connect directly to the validated IP, bypassing OS resolver
        return await super().connect_tcp(
            self.pinned_ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class SafePinnedTransport(httpx.AsyncHTTPTransport):
    """
    Transport that binds socket connection to a pre-validated IP,
    enforcing TLS SNI and Certificate verification against original hostname.
    """
    def __init__(self, pinned_ip: str, **kwargs):
        super().__init__(**kwargs)
        self.pinned_ip = pinned_ip
        # Recreate pool with PinnedBackend and no retries/connection sharing
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=self._pool._ssl_context,
            network_backend=PinnedBackend(pinned_ip),
            retries=0,
            http1=True,
            http2=False,
        )


@dataclass
class ExtractedPage:
    """Result of safe external web page extraction."""
    url: str
    final_url: str
    status_code: int
    title: str
    text_content: str
    byte_size: int
    content_type: str
    redirect_count: int


async def safe_fetch_page_content(
    url: str,
    max_redirects: int = 3,
    max_network_bytes: int = 200 * 1024,      # 200 KB compressed network stream
    max_decompressed_bytes: int = 500 * 1024,  # 500 KB decompressed text
    connect_timeout: float = 3.0,
    read_timeout: float = 4.0,
    total_timeout: float = 6.0,
) -> ExtractedPage:
    """
    Safely retrieves and extracts text content from an external web page with:
    - DNS pre-validation and private IP rejection on every hop
    - Anti-rebinding socket pinning with TLS SNI verification
    - Manual redirect re-validation (no automatic follow)
    - Streaming response limits to prevent zip-bomb / resource exhaustion
    - HTML text extraction with script/style stripping
    """
    current_url = url
    redirect_count = 0

    while True:
        parsed = urllib.parse.urlparse(current_url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise SSRFSecurityError(f"Prohibited URL scheme: {parsed.scheme} (only http/https permitted)")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFSecurityError(f"Missing hostname in URL: {current_url}")

        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

        # 1. DNS Pre-Resolution & Prohibited IP Family Check
        validated_ips = resolve_and_validate_hostname(hostname, port)
        pinned_ip = validated_ips[0]

        # 2. Ephemeral Client with SafePinnedTransport and trust_env=False
        transport = SafePinnedTransport(pinned_ip=pinned_ip, verify=True, trust_env=False)
        timeout_config = httpx.Timeout(
            total_timeout,
            connect=connect_timeout,
            read=read_timeout,
            write=read_timeout,
            pool=connect_timeout,
        )

        headers = {
            "User-Agent": "Problem2Project-ResearchBot/1.7 (+https://problem2project.ai)",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        }

        async with httpx.AsyncClient(
            transport=transport,
            trust_env=False,
            timeout=timeout_config,
            follow_redirects=False,
        ) as client:
            try:
                # Streaming GET to enforce size limits before reading entire response into RAM
                async with client.stream("GET", current_url, headers=headers) as response:
                    status_code = response.status_code

                    # Handle Redirects manually to re-validate destination IP
                    if status_code in (301, 302, 303, 307, 308):
                        if redirect_count >= max_redirects:
                            raise SSRFSecurityError(f"Redirect ceiling exceeded ({max_redirects} hops)")
                        location = response.headers.get("Location")
                        if not location:
                            raise SSRFSecurityError("Redirect response missing Location header")

                        next_url = urllib.parse.urljoin(current_url, location)
                        current_url = next_url
                        redirect_count += 1
                        continue

                    if status_code != 200:
                        raise SSRFSecurityError(f"HTTP error during page extraction: status {status_code}")

                    # Validate Content-Type
                    content_type = response.headers.get("Content-Type", "").lower()
                    if not any(t in content_type for t in ("text/html", "text/plain", "application/xhtml+xml")):
                        raise SSRFSecurityError(f"Unsupported content-type for research extraction: {content_type}")

                    # Stream network content with strict byte bounds
                    network_bytes = bytearray()
                    async for chunk in response.aiter_bytes():
                        network_bytes.extend(chunk)
                        if len(network_bytes) > max_network_bytes:
                            raise SSRFSecurityError(
                                f"Response exceeded max network stream limit ({max_network_bytes} bytes)"
                            )

                    # Decompressed content length check
                    try:
                        raw_text = network_bytes.decode(response.encoding or "utf-8", errors="replace")
                    except Exception:
                        raw_text = network_bytes.decode("latin-1", errors="replace")

                    if len(raw_text.encode("utf-8")) > max_decompressed_bytes:
                        raise SSRFSecurityError(
                            f"Decompressed text exceeded limit ({max_decompressed_bytes} bytes)"
                        )

                    # Extract text safely using BeautifulSoup
                    soup = bs4.BeautifulSoup(raw_text, "html.parser")
                    # Remove scripts, styles, metadata
                    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
                        tag.decompose()

                    title = ""
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()

                    extracted_text = soup.get_text(separator="\n", strip=True)
                    # Limit extracted text to 15,000 characters for LLM synthesis
                    capped_text = extracted_text[:15000]

                    return ExtractedPage(
                        url=url,
                        final_url=current_url,
                        status_code=status_code,
                        title=title,
                        text_content=capped_text,
                        byte_size=len(network_bytes),
                        content_type=content_type,
                        redirect_count=redirect_count,
                    )

            except SSRFSecurityError:
                raise
            except httpx.TimeoutException as exc:
                raise SSRFSecurityError(f"Timeout during extraction from '{hostname}': {exc}") from exc
            except (httpx.ConnectError, ssl.SSLError) as exc:
                raise SSRFSecurityError(f"Connection failure for '{hostname}': {exc}") from exc


def ssl_error_type():
    import ssl
    return (ssl.SSLError,)

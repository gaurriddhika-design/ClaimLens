"""URL validation helpers to reduce server-side request forgery risk.

DNS checks are repeated for every redirect. For production, enforce egress policy at
network level too; application checks alone cannot completely eliminate DNS rebinding.
"""
import ipaddress
import socket
from urllib.parse import urlsplit


class UnsafeURLError(ValueError):
    pass


def validate_public_http_url(url: str) -> str:
    try:
        parsed = urlsplit(url.strip())
        if parsed.scheme.lower() not in {"http", "https"}:
            raise UnsafeURLError("Only http and https URLs are allowed.")
        if not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise UnsafeURLError("URL must have a hostname and must not contain credentials.")
        if parsed.port is not None and not (1 <= parsed.port <= 65535):
            raise UnsafeURLError("URL port is invalid.")
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            raise UnsafeURLError("Local hostnames are not allowed.")
        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            try:
                records = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
            except socket.gaierror as exc:
                raise UnsafeURLError("URL hostname could not be resolved.") from exc
            addresses = [ipaddress.ip_address(record[4][0]) for record in records]
        if not addresses:
            raise UnsafeURLError("URL hostname has no address records.")
        for address in addresses:
            if not address.is_global:
                raise UnsafeURLError("URLs resolving to private, local, or reserved IP addresses are not allowed.")
        return url.strip()
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, UnsafeURLError):
            raise
        raise UnsafeURLError("URL is malformed.") from exc

from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings


def get_public_site_url(request=None) -> str:
    """
    URL pública base da aplicação (sem barra final).
    Prioridade: PUBLIC_SITE_URL > request (com proxy) > CSRF_TRUSTED_ORIGINS > ALLOWED_HOSTS.
    """
    explicit = (getattr(settings, "PUBLIC_SITE_URL", None) or "").strip().rstrip("/")
    if explicit:
        return explicit

    if request is not None:
        proto = (request.META.get("HTTP_X_FORWARDED_PROTO") or "").split(",")[0].strip()
        if not proto:
            proto = "https" if request.is_secure() else "http"
        host = (request.META.get("HTTP_X_FORWARDED_HOST") or "").split(",")[0].strip()
        if not host:
            try:
                host = request.get_host()
            except Exception:
                host = ""
        if host:
            return f"{proto}://{host}".rstrip("/")

    for origin in getattr(settings, "CSRF_TRUSTED_ORIGINS", []):
        origin = (origin or "").strip().rstrip("/")
        if origin and "*" not in origin:
            return origin

    for host in getattr(settings, "ALLOWED_HOSTS", []):
        host = (host or "").strip()
        if not host or host == "*" or host.startswith("."):
            continue
        return f"https://{host}"

    return "http://127.0.0.1:8000"


def absolute_url(path: str, *, request=None) -> str:
    """Junta o path (ex.: / ou /conta/password_reset/) à URL pública."""
    base = get_public_site_url(request)
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


def email_site_parts(request=None) -> tuple[str, str]:
    """Retorna (protocol, domain) para e-mails do Django auth."""
    parsed = urlparse(get_public_site_url(request))
    protocol = parsed.scheme or "https"
    domain = parsed.netloc or parsed.path.split("/")[0]
    return protocol, domain

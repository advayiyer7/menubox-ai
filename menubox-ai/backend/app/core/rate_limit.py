"""
Rate limiting (slowapi). Keyed by client IP, honouring X-Forwarded-For so it
works correctly behind the Render / Vercel proxies in production.

Per-route limits are declared with @limiter.limit(...) on the routers. The
limiter and its 429 handler are registered in app.main.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _client_ip(request: Request) -> str:
    """Best-effort real client IP, trusting the proxy's X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_client_ip)

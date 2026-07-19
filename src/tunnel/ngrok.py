"""Optional ngrok tunnel lifecycle (pyngrok)."""

from __future__ import annotations

from src.config import SETTINGS

try:
    from pyngrok import ngrok, conf
except ImportError:
    ngrok = None  # type: ignore[assignment]


def start_tunnel() -> str | None:
    """Start ngrok tunnel and return the public URL, or None if unavailable."""
    if ngrok is None:
        print("pyngrok not installed. Run: pip install pyngrok")
        return None

    if SETTINGS.ngrok_token:
        conf.get_default().auth_token = SETTINGS.ngrok_token  # type: ignore[union-attr]

    # If a reserved domain is configured, use it; otherwise get a random URL
    addr = f"localhost:{SETTINGS.port}"
    if SETTINGS.ngrok_domain:
        public_url = ngrok.connect(addr, bind_tls=True, domain=SETTINGS.ngrok_domain)
    else:
        public_url = ngrok.connect(addr, bind_tls=True)

    url = public_url.public_url
    print(f"🌍 Tunnel active: {url}")
    print(f"   TradingView webhook URL: {url}/webhook/tradingview")
    return url

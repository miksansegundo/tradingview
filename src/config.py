"""Configuration — loaded once from .env on startup."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # Webhook security (TradingView can include a secret in the payload)
    webhook_secret: str | None = os.getenv("WEBHOOK_SECRET")

    # Paper trading defaults
    default_symbol: str = os.getenv("DEFAULT_SYMBOL", "MPL")  # Micro Platinum
    default_qty: int = int(os.getenv("DEFAULT_QTY", "1"))

    # Database
    db_path: str = os.getenv("DB_PATH", "data/paper_trading.db")

    # Ngrok (optional)
    ngrok_token: str | None = os.getenv("NGROK_TOKEN")
    ngrok_domain: str | None = os.getenv("NGROK_DOMAIN")


SETTINGS = Settings()

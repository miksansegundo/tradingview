# TradingView Paper Trader

Automated trading system for Micro Platinum (MPL) futures on TradingView — paper trading only.

## Phases

- **Phase 1** (current): Webhook receiver + paper trading engine. Establish the connection and hooks to control TradingView.
- **Phase 2** (future): Implement the trading strategy.

## Quick Start

```bash
pip install -r requirements.txt
python -m src.main
```

See `http://localhost:8000/docs` for Swagger UI.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Server health check |
| `/webhook/tradingview` | POST | Receive TradingView strategy alerts |
| `/docs` | GET | Swagger UI |

## Running the Server

```bash
python -m src.main
```

The server starts on `http://localhost:8000` by default. Set `PORT` in `.env` to change.

## Exposing with ngrok

TradingView needs a public URL to send webhook alerts. ngrok creates a secure tunnel to your local server.

1. Sign up at https://ngrok.com and get your auth token.
2. Set `NGROK_TOKEN=your_token` in `.env`.
3. (Optional) Reserve a domain in ngrok dashboard and set `NGROK_DOMAIN=your-domain.ngrok-free.app` in `.env`.
4. Start the tunnel:

```bash
python -c "from src.tunnel.ngrok import start_tunnel; start_tunnel()"
```

This prints a public URL like `https://abc123.ngrok-free.app`. Configure this in TradingView's alert webhook settings.

## Configuring TradingView

1. Write a Pine Script strategy (or use an existing one).
2. Create an Alert → select your strategy → "More" → Webhook URL.
3. Set the webhook URL to `https://your-ngrok-domain.ngrok-free.app/webhook/tradingview`.
4. In the alert message JSON body, use this format:

```json
{
  "ticker": "CME_MINI:MPL1!",
  "action": "buy",
  "price": {{close}},
  "signal_id": "sig_{{timenow}}"
}
```

### Alert Actions

| Action | Behavior |
|---|---|
| `buy` | Open long (if flat) or error (if already long) |
| `sell` | Open short (if flat) or error (if already short) |
| `exit` / `exit_long` | Close long position |
| `exit_short` | Close short position |
| `close_all` | Close current position regardless of direction |

## Configuration (.env)

```
HOST=0.0.0.0
PORT=8000
DEFAULT_SYMBOL=MPL
DEFAULT_QTY=1
DB_PATH=data/paper_trading.db
# WEBHOOK_SECRET=your-secret-here
# NGROK_TOKEN=your-token
# NGROK_DOMAIN=your-domain.ngrok-free.app
```

## Paper Trading Database

SQLite database at `DB_PATH` (default: `data/paper_trading.db`).

| Table | Description |
|---|---|
| `orders` | Every signal processed — open, close, or rejected |
| `positions` | Current open positions (one per symbol, upserted) |
| `trade_log` | Timestamped events: signals received, orders filled, errors |


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

### SSH tunnel (recommended)

Add your SSH public key to ngrok at https://dashboard.ngrok.com/tunnels/ssh-keys, then:

```bash
ssh -R 443:localhost:8000 v2@connect.ngrok-agent.com http
```

This prints a public URL like `https://saucy-manicure-quickstep.ngrok-free.dev`. The first time you connect, it adds the host key to `known_hosts` automatically.

### Testing locally with curl

When testing through the ngrok URL with curl, add the bypass header:

```bash
curl -H "ngrok-skip-browser-warning: true" https://your-tunnel.ngrok-free.dev/health
```

TradingView's server-side webhook requests work without this header — they use a non-browser User-Agent and bypass the interstitial automatically.

## Configuring TradingView

1. Copy `scripts/mpl_paper_trader_template.pine` into the Pine Editor.
2. Add your strategy logic (the template has `// Phase 2` markers).
3. Create an Alert → select your strategy → "More" → Webhook URL.
4. Set the webhook URL to `https://your-ngrok-domain.ngrok-free.app/webhook/tradingview`.
5. In the alert message JSON body, use this format:

```json
{
  "ticker": "{{ticker}}",
  "action": "{{strategy.order.alert_message}}",
  "price": {{strategy.order.price}},
  "qty": 1,
  "signal_id": "sig_{{timenow}}",
  "strategy": "MPL Paper Trader Template"
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


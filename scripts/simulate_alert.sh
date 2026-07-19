#!/usr/bin/env bash
# Simulate a TradingView strategy alert webhook POST.
# Usage: ./scripts/simulate_alert.sh [buy|sell|exit_long|exit_short|close_all]

ACTION="${1:-buy}"
HOST="${HOST:-http://localhost:8000}"

PAYLOAD=$(cat <<JSON
{
  "ticker": "MPL",
  "action": "$ACTION",
  "price": 950.50,
  "qty": 1,
  "signal_id": "sig_manual_$(date +%s)",
  "strategy": "manual_test"
}
JSON
)

echo "→ Sending: $ACTION to $HOST/webhook/tradingview"
echo "$PAYLOAD" | python3 -m json.tool

curl -s -X POST "$HOST/webhook/tradingview" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" | python3 -m json.tool

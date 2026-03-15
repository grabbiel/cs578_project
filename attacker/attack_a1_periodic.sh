#!/bin/bash
set -e

DELAY_MS="${1:?Usage: $0 <delay_ms> <on_sec> <off_sec> <interface> <duration>}"
ON_SEC="${2:?Usage: $0 <delay_ms> <on_sec> <off_sec> <interface> <duration>}"
OFF_SEC="${3:?Usage: $0 <delay_ms> <on_sec> <off_sec> <interface> <duration>}"
IF_S="${4:?Usage: $0 <delay_ms> <on_sec> <off_sec> <interface> <duration>}"
DURATION="${5:?Usage: $0 <delay_ms> <on_sec> <off_sec> <interface> <duration>}"

echo "============================================="
echo " Attack A1 (Periodic) — Delay Spikes"
echo " Delay: ${DELAY_MS}ms"
echo " Pattern: ${ON_SEC}s on / ${OFF_SEC}s off"
echo " Duration: ${DURATION}s"
echo "============================================="

sudo pfctl -F all 2>/dev/null || true
sudo dnctl -q flush 2>/dev/null || true

sudo dnctl pipe 1 config delay "${DELAY_MS}"

START_TIME=$(date +%s)
CYCLE=0

while true; do
  ELAPSED=$(($(date +%s) - START_TIME))
  if [ "$ELAPSED" -ge "$DURATION" ]; then
    break
  fi

  CYCLE=$((CYCLE + 1))

  echo "[A1-Periodic] Cycle $CYCLE: Delay ON (${DELAY_MS}ms) at ${ELAPSED}s"
  cat <<EOF | sudo pfctl -a rledbat_attack -f -
dummynet in on $IF_S proto tcp from 10.0.1.1 to 10.0.2.100 pipe 1
EOF
  sudo pfctl -e 2>/dev/null || true
  sleep "$ON_SEC"

  ELAPSED=$(($(date +%s) - START_TIME))
  if [ "$ELAPSED" -ge "$DURATION" ]; then
    break
  fi

  echo "[A1-Periodic] Cycle $CYCLE: Delay OFF at ${ELAPSED}s"
  sudo pfctl -a rledbat_attack -F rules 2>/dev/null || true
  sleep "$OFF_SEC"
done

sudo pfctl -F all 2>/dev/null || true
sudo dnctl -q flush 2>/dev/null || true
echo ""
echo "[A1-Periodic] Attack complete after ${DURATION}s ($CYCLE cycles)"

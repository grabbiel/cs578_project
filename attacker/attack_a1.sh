#!/bin/bash
set -e

DELAY_MS="${1:?Usage: $0 <delay_ms> <interface_from_S>}"
IF_S="${2:?Usage: $0 <delay_ms> <interface_from_S>}"

echo "============================================="
echo " Attack A1 — Delay Inflation"
echo " Injected delay: ${DELAY_MS}ms"
echo " Interface: $IF_S"
echo "============================================="

sudo pfctl -F all 2>/dev/null || true
sudo dnctl -q flush 2>/dev/null || true

sudo dnctl pipe 1 config delay "${DELAY_MS}"

cat <<EOF | sudo pfctl -a rledbat_attack -f -
dummynet in on $IF_S proto tcp from 10.0.1.1 to 10.0.2.100 pipe 1
EOF

sudo pfctl -e 2>/dev/null || true

echo ""
echo "[A1] Delay pipe created: ${DELAY_MS}ms on forward path"
echo "[A1] Affecting: TCP traffic from 10.0.1.1 → 10.0.2.100"
echo "[A1] Attack is ACTIVE"
echo "[A1] Run ./teardown.sh to stop"

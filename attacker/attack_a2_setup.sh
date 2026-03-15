#!/bin/bash

set -e

IF_S="${1:?Usage: $0 <interface_from_S> <interface_to_router>}"
IF_R="${2:?Usage: $0 <interface_from_S> <interface_to_router>}"

echo "============================================="
echo " Attack A2 — Kernel Setup"
echo " Blocking kernel forwarding for target flow"
echo " Scapy will handle forwarding instead"
echo "============================================="

# Clear previous rules
sudo pfctl -F all 2>/dev/null || true

cat <<EOF | sudo pfctl -a rledbat_attack -f -
block in on $IF_S proto tcp from 10.0.1.1 to 10.0.2.100

# Also block return path (ACKs from Host R to Host S)
# so Scapy can handle bidirectional manipulation if needed
block in on $IF_R proto tcp from 10.0.2.100 to 10.0.1.1
EOF

sudo pfctl -e 2>/dev/null || true

echo ""
echo "[A2-Setup] Kernel forwarding blocked for target flow"
echo "[A2-Setup] Now run the Scapy attack script (attack_a2.py)"
echo "[A2-Setup] Run ./teardown.sh when done to restore normal forwarding"

#!/bin/bash

IF="${1:?Usage: $0 <interface>}"

echo "[Sniff] Listening for TCP connections from 10.0.1.1 to 10.0.2.100..."
echo "[Sniff] Start the BITS transfer on Host R if not already running."
echo "[Sniff] Press Ctrl+C after you see the connection."
echo ""

sudo tcpdump -i "$IF" -nn \
  "src host 10.0.1.1 and dst host 10.0.2.100 and tcp" \
  -c 20 2>/dev/null |
  awk '{print $3, "→", $5}' |
  sort -u

echo ""
echo "[Sniff] Look for the source port (e.g., 10.0.1.1.XXXXX → 10.0.2.100.8080)"
echo "[Sniff] Use that port number as --sport for attack_a3.py"

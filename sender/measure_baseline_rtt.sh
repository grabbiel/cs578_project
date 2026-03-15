#!/bin/bash

OUTPUT_DIR="$HOME/rledbat-testbed/results/baseline_rtt"
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$OUTPUT_DIR/ping_${TIMESTAMP}.txt"

echo "[RTT] Sending 100 pings to Host R (10.0.2.100)..."
echo "[RTT] Results will be saved to: $OUTPUT_FILE"
echo ""

ping -c 100 -i 0.1 10.0.2.100 | tee "$OUTPUT_FILE"

echo ""
echo "[RTT] Done. Check min/avg/max/stddev in t

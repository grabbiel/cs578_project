#!/bin/bash

set -e

EXPERIMENT="${1:?Usage: $0 <experiment_name> <duration> <if_S> <if_R>}"
DURATION="${2:?Usage: $0 <experiment_name> <duration> <if_S> <if_R>}"
IF_S="${3:?Usage: $0 <experiment_name> <duration> <if_S> <if_R>}"
IF_R="${4:?Usage: $0 <experiment_name> <duration> <if_S> <if_R>}"

LOG_DIR="$HOME/rledbat-testbed/results/${EXPERIMENT}"
mkdir -p "$LOG_DIR"

echo "============================================="
echo " Packet Capture — $EXPERIMENT"
echo " Duration: ${DURATION}s"
echo " Captures: $LOG_DIR"
echo "============================================="

echo "[Capture] Starting capture on $IF_S (Subnet A side)..."
sudo tcpdump -i "$IF_S" -w "$LOG_DIR/capture_subnet_a.pcap" \
  -s 96 \
  "host 10.0.1.1 and host 10.0.2.100" &
PID_A=$!

echo "[Capture] Starting capture on $IF_R (Subnet B side)..."
sudo tcpdump -i "$IF_R" -w "$LOG_DIR/capture_subnet_b.pcap" \
  -s 96 \
  "host 10.0.1.1 and host 10.0.2.100" &
PID_B=$!

sleep 1
echo "[Capture] Both captures running."
echo "[Capture] Waiting ${DURATION}s..."

sleep "$DURATION"

echo "[Capture] Stopping..."
sudo kill "$PID_A" "$PID_B" 2>/dev/null
wait "$PID_A" "$PID_B" 2>/dev/null

echo ""
echo "[Capture] Complete. Files:"
ls -lh "$LOG_DIR"/capture_*.pcap

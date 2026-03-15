#!/bin/bash

set -e

EXPERIMENT_NAME="${1:?Usage: $0 <experiment_name> <duration_seconds>}"
DURATION="${2:?Usage: $0 <experiment_name> <duration_seconds>}"
INTERFACE="en15"
HTTP_PORT=8080
IPERF_PORT=5201
SERVE_DIR="$HOME/rledbat-testbed"
LOG_DIR="$HOME/rledbat-testbed/results/${EXPERIMENT_NAME}"

mkdir -p "$LOG_DIR"
echo "============================================="
echo " Host S — Experiment: $EXPERIMENT_NAME"
echo " Duration: ${DURATION}s"
echo " Interface: $INTERFACE"
echo " Results: $LOG_DIR"
echo "============================================="

echo ""
echo "[Check] Pinging Host A (10.0.1.2)..."
ping -c 2 -W 2 10.0.1.2 >/dev/null 2>&1 || {
  echo "ERROR: Cannot reach Host A"
  exit 1
}
echo "[Check] Pinging Host R (10.0.2.100)..."
ping -c 2 -W 2 10.0.2.100 >/dev/null 2>&1 || {
  echo "ERROR: Cannot reach Host R"
  exit 1
}
echo "[Check] Connectivity OK"

echo ""
echo "[Capture] Starting tcpdump on $INTERFACE..."
sudo tcpdump -i "$INTERFACE" -w "$LOG_DIR/sender_capture.pcap" \
  "host 10.0.2.100" \
  -s 96 &
TCPDUMP_PID=$!
sleep 1

echo "[HTTP] Starting file server on port $HTTP_PORT..."
cd "$SERVE_DIR"
python3 -m http.server "$HTTP_PORT" --bind 10.0.1.1 \
  >"$LOG_DIR/http_server.log" 2>&1 &
HTTP_PID=$!
sleep 1

echo "[iperf3] Starting iperf3 server on port $IPERF_PORT..."
iperf3 -s -p "$IPERF_PORT" --bind 10.0.1.1 --json \
  --logfile "$LOG_DIR/iperf3_server.json" &
IPERF_PID=$!
sleep 1

echo "[Info] Recording system information..."
{
  echo "Experiment: $EXPERIMENT_NAME"
  echo "Date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "Duration: ${DURATION}s"
  echo "Hostname: $(hostname)"
  echo "macOS: $(sw_vers -productVersion)"
  echo "Interface: $INTERFACE"
  echo ""
  echo "--- Network Configuration ---"
  ifconfig "$INTERFACE"
  echo ""
  echo "--- Routing Table ---"
  netstat -rn | grep -E "(10\.0\.|default)"
  echo ""
  echo "--- TCP Settings ---"
  sysctl net.inet.tcp.rfc1323
  sysctl net.inet.tcp.mssdflt
  sysctl net.inet.tcp.sendspace
  sysctl net.inet.tcp.recvspace
} >"$LOG_DIR/system_info.txt" 2>&1

echo ""
echo "============================================="
echo " Servers running. Waiting ${DURATION}s..."
echo " HTTP:   http://10.0.1.1:$HTTP_PORT/testfile.bin"
echo " iperf3: 10.0.1.1:$IPERF_PORT"
echo "============================================="
echo ""
echo " >>> Start the transfer on Host R now <<<"
echo ""

sleep "$DURATION"

echo ""
echo "[Cleanup] Stopping services..."

if kill -0 "$IPERF_PID" 2>/dev/null; then
  kill "$IPERF_PID" 2>/dev/null
  wait "$IPERF_PID" 2>/dev/null
  echo "[iperf3] Stopped"
fi

if kill -0 "$HTTP_PID" 2>/dev/null; then
  kill "$HTTP_PID" 2>/dev/null
  wait "$HTTP_PID" 2>/dev/null
  echo "[HTTP] Stopped"
fi

if kill -0 "$TCPDUMP_PID" 2>/dev/null; then
  sudo kill "$TCPDUMP_PID" 2>/dev/null
  wait "$TCPDUMP_PID" 2>/dev/null
  echo "[Capture] Stopped"
fi

echo ""
echo "============================================="
echo " Experiment complete: $EXPERIMENT_NAME"
echo " Results saved to: $LOG_DIR"
echo "============================================="
echo ""
ls -lh "$LOG_DIR"

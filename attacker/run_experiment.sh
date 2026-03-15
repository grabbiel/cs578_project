#!/bin/bash

set -e

EXPERIMENT="${1:?Usage: $0 <name> <duration> <if_S> <if_R> [attack_cmd...]}"
DURATION="${2:?Usage: $0 <name> <duration> <if_S> <if_R> [attack_cmd...]}"
IF_S="${3:?Usage: $0 <name> <duration> <if_S> <if_R> [attack_cmd...]}"
IF_R="${4:?Usage: $0 <name> <duration> <if_S> <if_R> [attack_cmd...]}"
shift 4
ATTACK_CMD="$@"

LOG_DIR="$HOME/rledbat-testbed/results/${EXPERIMENT}"
SCRIPT_DIR="$HOME/rledbat-testbed/scripts"
mkdir -p "$LOG_DIR"

echo "============================================="
echo " Host A — Experiment: $EXPERIMENT"
echo " Duration: ${DURATION}s"
echo " Interfaces: $IF_S (Subnet A), $IF_R (Subnet B)"
if [ -n "$ATTACK_CMD" ]; then
  echo " Attack: $ATTACK_CMD"
else
  echo " Attack: None (baseline)"
fi
echo " Results: $LOG_DIR"
echo "============================================="

echo ""
echo "[Step 1] Cleaning previous state..."
"$SCRIPT_DIR/teardown.sh"

echo ""
echo "[Step 2] Recording system info..."
{
  echo "Experiment: $EXPERIMENT"
  echo "Date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "Duration: ${DURATION}s"
  echo ""
  echo "--- Interface $IF_S (Subnet A) ---"
  ifconfig "$IF_S"
  echo ""
  echo "--- Interface $IF_R (Subnet B) ---"
  ifconfig "$IF_R"
  echo ""
  echo "--- IP Forwarding ---"
  sysctl net.inet.ip.forwarding
  echo ""
  echo "--- Attack Command ---"
  echo "$ATTACK_CMD"
} >"$LOG_DIR/system_info.txt" 2>&1

echo ""
echo "[Step 3] Starting packet captures..."
"$SCRIPT_DIR/capture.sh" "$EXPERIMENT" "$DURATION" "$IF_S" "$IF_R" &
CAPTURE_PID=$!
sleep 2

if [ -n "$ATTACK_CMD" ]; then
  echo ""
  echo "[Step 4] Launching attack..."
  cd "$SCRIPT_DIR"
  $ATTACK_CMD &
  ATTACK_PID=$!
  sleep 1
  echo "[Step 4] Attack launched (PID: $ATTACK_PID)"
else
  echo ""
  echo "[Step 4] No attack (baseline run)"
  ATTACK_PID=""
fi

echo ""
echo "============================================="
echo " >>> Start the transfer on Host R now <<<"
echo " >>> Start iperf3 on Host R if needed  <<<"
echo "============================================="
echo ""
echo "[Step 5] Waiting ${DURATION}s..."
sleep "$DURATION"

echo ""
echo "[Step 6] Cleaning up..."

if [ -n "$ATTACK_PID" ] && kill -0 "$ATTACK_PID" 2>/dev/null; then
  sudo kill "$ATTACK_PID" 2>/dev/null
  wait "$ATTACK_PID" 2>/dev/null
  echo "[Cleanup] Attack stopped"
fi

wait "$CAPTURE_PID" 2>/dev/null
echo "[Cleanup] Captures stopped"

"$SCRIPT_DIR/teardown.sh"

echo ""
echo "============================================="
echo " Experiment complete: $EXPERIMENT"
echo " Results: $LOG_DIR"
echo "============================================="
echo ""
ls -lh "$LOG_DIR"

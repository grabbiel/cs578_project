#!/bin/bash

echo "[Teardown] Clearing pfctl rules..."
sudo pfctl -F all 2>/dev/null || true
sudo pfctl -d 2>/dev/null || true

echo "[Teardown] Flushing dummynet pipes..."
sudo dnctl -q flush 2>/dev/null || true

echo "[Teardown] Killing any running Scapy processes..."
sudo pkill -f "python3.*scapy" 2>/dev/null || true
sudo pkill -f "python3.*attack_a" 2>/dev/null || true

echo "[Teardown] Verifying IP forwarding is still enabled..."
sudo sysctl -w net.inet.ip.forwarding=1

echo "[Teardown] Done. Host A is in clean forwarding state."

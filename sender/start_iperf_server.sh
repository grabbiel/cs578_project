#!/bin/bash

PORT=5201

echo "[iperf3 Server] Listening on port: $PORT"
echo "[iperf3 Server] Waiting for connections from Host R (10.0.2.100)..."
echo "[iperf3 Server] Press Ctrl+C to stop"
echo ""

iperf3 -s -p "$PORT" --bind 10.0.1.1

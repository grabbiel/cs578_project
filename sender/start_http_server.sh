#!/bin/bash

PORT=8080
SERVE_DIR="$HOME/rledbat-testbed"

echo "[HTTP Server] Serving files from: $SERVE_DIR"
echo "[HTTP Server] Listening on port: $PORT"
echo "[HTTP Server] Test file URL: http://10.0.1.1:$PORT/testfile.bin"
echo "[HTTP Server] Press Ctrl+C to stop"
echo ""

cd "$SERVE_DIR"
python3 -m http.server "$PORT" --bind 10.0.1.1

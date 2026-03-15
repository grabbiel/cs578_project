#!/bin/bash

set -e

IF_S="${1:?Usage: $0 <interface_to_S> <interface_to_router>}"
IF_R="${2:?Usage: $0 <interface_to_S> <interface_to_router>}"

echo "============================================="
echo " Host A — Setup"
echo " Interface to Host S: $IF_S"
echo " Interface to Router: $IF_R"
echo "============================================="

echo "[Setup] Disabling Wi-Fi..."
sudo networksetup -setairportpower en0 off

echo "[Setup] Assigning IP addresses..."
sudo ifconfig "$IF_S" 10.0.1.2 netmask 255.255.255.0 up
sudo ifconfig "$IF_R" 10.0.2.1 netmask 255.255.255.0 up

echo "[Setup] Enabling IP forwarding..."
sudo sysctl -w net.inet.ip.forwarding=1

echo "[Setup] Clearing previous pfctl/dummynet rules..."
sudo pfctl -F all 2>/dev/null || true
sudo dnctl -q flush 2>/dev/null || true

echo ""
echo "[Verify] Interface $IF_S:"
ifconfig "$IF_S" | grep "inet "
echo "[Verify] Interface $IF_R:"
ifconfig "$IF_R" | grep "inet "
echo "[Verify] IP forwarding:"
sysctl net.inet.ip.forwarding
echo "[Verify] TCP timestamps:"
sysctl net.inet.tcp.rfc1323

echo ""
echo "[Test] Pinging Host S (10.0.1.1)..."
ping -c 2 -W 2 10.0.1.1 >/dev/null 2>&1 && echo "  OK" || echo "  FAILED"
echo "[Test] Pinging Host R (10.0.2.100)..."
ping -c 2 -W 2 10.0.2.100 >/dev/null 2>&1 && echo "  OK" || echo "  FAILED"

echo ""
echo "[Setup] Complete. Host A is ready as a router."

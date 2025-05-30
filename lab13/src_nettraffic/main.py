import os
import sys
import threading
import time
from collections import defaultdict

from scapy.all import sniff, IP, TCP, UDP
from prettytable import PrettyTable
import argparse
import netifaces


# Track incoming and outgoing traffic
# (proto, port) -> bytes amount
incoming, outgoing = defaultdict(int), defaultdict(int)

lock = threading.Lock()


def get_ips(all_interfaces: bool):
    local_ips = set()

    default_interface = netifaces.gateways()["default"][netifaces.AF_INET][1]
    interfaces = netifaces.interfaces() if all_interfaces else [default_interface]
    for iface in interfaces:
        addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
        for addr in addrs:
            ip = addr.get("addr")
            if ip:
                local_ips.add(ip)
    return local_ips


def process_packet(pkt, local_ips):
    if not IP in pkt:
        return

    ip = pkt[IP]
    proto, sport, dport = None, None, None
    if TCP in pkt:
        proto = "TCP"
        sport, dport = pkt[TCP].sport, pkt[TCP].dport
        size = len(pkt[TCP])
    elif UDP in pkt:
        proto = "UDP"
        sport, dport = pkt[UDP].sport, pkt[UDP].dport
        size = len(pkt[UDP])
    else:
        return

    # Determine direction based on IP addresses
    if ip.src in local_ips:
        key = (proto, sport, ip.dst)
        with lock:
            outgoing[key] += size
    elif ip.dst in local_ips:
        key = (proto, dport, ip.src)
        with lock:
            incoming[key] += size
    else:
        # Not our traffic
        return


def print_stats(update_interval: int):
    """
    Clears the terminal and prints the current statistics in the following table format:
    Protocol | Port | Address | Incoming (bytes) | Outgoing (bytes)
    """
    os.system("cls" if os.name == "nt" else "clear")  # clear terminal

    table = PrettyTable()
    table.field_names = ["Protocol", "Port", "Address", "Incoming (B)", "Outgoing (B)"]

    all_keys = set(incoming.keys()) | set(outgoing.keys())
    for key in sorted(all_keys):
        proto, port, addr = key
        inc, out = incoming.get(key, 0), outgoing.get(key, 0)
        table.add_row([proto, port, addr, inc, out])

    print(table)
    print(f"(Update every {update_interval} sec - press Ctrl+C to exit)")


def stats_loop(update_interval: int):
    try:
        while True:
            time.sleep(update_interval)
            with lock:
                print_stats(update_interval)
    except KeyboardInterrupt:
        print("\nUser interrupt has been detected. Shutting down...")
        sys.exit(0)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Network traffic monitor")
    parser.add_argument(
        "-u",
        "--update-interval",
        type=int,
        default=1,
        help="Interval in seconds to update the statistics",
    )
    parser.add_argument(
        "-a",
        "--all-interfaces",
        action="store_true",
        help="Capture traffic on all interfaces",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    local_ips = get_ips(args.all_interfaces)

    # Statistics printout thread
    t = threading.Thread(target=stats_loop, args=(args.update_interval,), daemon=True)
    t.start()

    # Capturing packets on all interfaces
    sniff(prn=lambda packet: process_packet(packet, local_ips), store=False)

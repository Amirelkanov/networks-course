import os
import socket
import struct
import time
import select
import sys
import argparse
from const import BUF_SIZE, ICMP_ECHO_REQUEST, ICMP_ECHO_REPLY, ICMP_TIME_EXCEEDED


def checksum(icmp_packet: bytes) -> int:
    checksum = 0
    for i in range(0, len(icmp_packet), 2):
        checksum += (icmp_packet[i] << 8) + (
            struct.unpack("B", icmp_packet[i + 1 : i + 2])[0]
            if len(icmp_packet[i + 1 : i + 2])
            else 0
        )

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum = ~checksum & 0xFFFF
    return checksum


# Creates ICMP packet with current time as data
def create_packet(identifier, sequence_number):
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, 0, identifier, sequence_number)
    data = struct.pack("!d", time.time())
    chksum = checksum(header + data)
    # Repack header with real checksum
    header = struct.pack(
        "!BBHHH", ICMP_ECHO_REQUEST, 0, chksum, identifier, sequence_number
    )
    return header + data


# Returns (ip, recv_time) or (None, None) if no reply received / error occurred
def recv_icmp_packet(sock, timeout):
    try:
        ready = select.select([sock], [], [], timeout)
        if ready[0] == []:  # timeout
            return (None, None)
        recv_packet, addr = sock.recvfrom(BUF_SIZE)
        icmp_header = recv_packet[20 : 20 + 8]
        icmp_type, _, _, _, _ = struct.unpack("!BBHHH", icmp_header)
        if icmp_type in [ICMP_ECHO_REPLY, ICMP_TIME_EXCEEDED]:
            recv_time = time.time()
            return (addr[0], recv_time)
        return (None, None)
    except socket.error:
        return (None, None)


def sprint_host_with_address(host: str, address: str):
    return f"{host}{ f' [{address}]' if address and host != address else '' }"


def traceroute(host: str, max_hops: int, probes: int, timeout: float):
    try:
        dest_addr = socket.gethostbyname(host)
    except socket.gaierror as e:
        print(f"Cannot resolve {host}: {e}")
        sys.exit(1)

    print(f"Tracing route to {sprint_host_with_address(host, dest_addr)} ")
    print(f"over a maximum of {max_hops} hops with {probes} probes each:\n")

    identifier = os.getpid() & 0xFFFF
    sequence_number = 0

    for ttl in range(1, max_hops + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.settimeout(timeout)

        print(f" {ttl:>2}", end="\t", flush=True)
        display_addr, display_host = None, None
        for _ in range(probes):
            sequence_number += 1
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

            packet = create_packet(identifier, sequence_number)
            send_time = time.time()
            sock.sendto(packet, (dest_addr, 0))

            curr_addr, recv_time = recv_icmp_packet(sock, timeout)

            display_addr = curr_addr if display_addr is None else display_addr
            rtt = (recv_time - send_time) * 1000 if curr_addr else None
            print(f"{int(rtt):3d} ms" if rtt else f"{'  *':>6}", end="\t", flush=True)

        if display_addr:
            try:
                display_host = socket.gethostbyaddr(display_addr)[0]
            except socket.herror:
                display_host = display_addr
            print(
                sprint_host_with_address(display_host, display_addr),
                end="\n",
                flush=True,
            )
        else:
            print(f"Request timed out.", end="\n", flush=True)

        if display_addr == dest_addr:
            print("\nTrace complete.\n")
            break

        sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="tracert using ICMP echo requests")
    parser.add_argument("host", help="Destination host to trace route to")
    parser.add_argument(
        "-m",
        "--max-hops",
        type=int,
        default=30,
        help="Max hops (max TTL to be reached)",
    )
    parser.add_argument(
        "-p", "--probes", type=int, default=3, help="Number of probes per hop"
    )
    parser.add_argument(
        "-w",
        "--wait",
        type=float,
        default=3.0,
        help="Timeout to wait for each reply (in seconds)",
    )
    args = parser.parse_args()

    traceroute(args.host, args.max_hops, args.probes, args.wait)

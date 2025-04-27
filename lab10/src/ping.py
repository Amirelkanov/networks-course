import os
import sys
import socket
import struct
import time
from statistics import mean, stdev
import argparse
from typing import Tuple
from const import ICMP_DEST_UNREACH, ICMP_ECHO_REQUEST, ICMP_ECHO_REPLY, ICMP_UNREACH_CODES, BUF_SIZE

def checksum(icmp_packet):
    checksum = 0
    for i in range(0, len(icmp_packet), 2):
        checksum += (icmp_packet[i] << 8) + (
            struct.unpack('B', icmp_packet[i + 1:i + 2])[0]
            if len(icmp_packet[i + 1:i + 2]) else 0
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
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, chksum, identifier, sequence_number)
    return header + data


# Returns (ttl, rtt) and error message (hello golang)
def parse_reply(packet, identifier, sequence_number, addr) -> Tuple[Tuple[int, float], str]:
    ip_header_len = 20
    icmp_header = packet[ip_header_len:ip_header_len + 8]
    type, code, _, pkt_id, pkt_seq = struct.unpack("!BBHHH", icmp_header)

    if type == ICMP_DEST_UNREACH:
        msg = ICMP_UNREACH_CODES.get(code, f"Unreachable, code {code}")
        return ((None, None), msg)

    # Ignore other ICMP packets
    if type != ICMP_ECHO_REPLY or pkt_id != identifier or pkt_seq != sequence_number:
        return ((None, None), None)

    # I'm sending timestamp (which is double) in data field and when the response from the server comes,
    # I can simply extract this date to calculate RTT
    time_data = packet[ip_header_len + 8:ip_header_len + 8 + struct.calcsize("!d")]
    time_recv = time.time()
    time_orig = struct.unpack("!d", time_data)[0]
    rtt = (time_recv - time_orig) * 1000
    
    ttl = packet[8]
    return ((ttl, rtt), None)


def ping(host, count, timeout):
    try:
        dest_addr = socket.gethostbyname(host)
    except socket.gaierror as e:
        print(f"Cannot resolve {host}: {e}")
        sys.exit(1)

    print(f"PING {host} ({dest_addr}) {struct.calcsize('!d')} bytes of data.")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    sock.settimeout(timeout)

    identifier = os.getpid() & 0xFFFF # I think it's kinda unique ID for each process
    rtts = []
    sent, received = 0, 0

    try:
        for seq in range(1, count + 1):
            try:
                packet = create_packet(identifier, seq)
                sent += 1
                sock.sendto(packet, (dest_addr, 1))
                
                recv_packet, addr = sock.recvfrom(BUF_SIZE)
                (ttl, rtt), error = parse_reply(recv_packet, identifier, seq, addr)
                info = f"icmp_seq={seq} ttl={ttl} time={rtt:.3f} ms" if not error else error
                if not error: 
                    received += 1
                    rtts.append(rtt)
                print(f"{len(recv_packet)} bytes from {addr[0]}: {info}") 
            except socket.timeout:
                print(f"Request timeout for icmp_seq {seq}")
            except socket.error as e:
                print(f"Socket error: {e}")
            finally:
                time.sleep(timeout)
    except KeyboardInterrupt:
        pass
    finally:
        loss_pct = ((sent - received) / sent) * 100
        print(f"\n--- {host} ping statistics ---")
        print(f"{sent} packets transmitted, {received} received, {loss_pct:.0f}% packet loss")
        if rtts:
            std = round(stdev(rtts), 3) if len(rtts) > 1 else "NaN"
            print(f"rtt min/avg/max/mdev = {min(rtts):.3f}/{mean(rtts):.3f}/{max(rtts):.3f}/{std} ms")
        else:
            print("No packets received")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ping utility for lab10')
    parser.add_argument('host', help='Host to ping')
    parser.add_argument('-c', '--count', type=int, default=4, help='Number of requests to send')
    parser.add_argument('-t', '--timeout', type=float, default=1, help='Timeout in seconds')
    args = parser.parse_args()
    ping(args.host, count=args.count, timeout=args.timeout)

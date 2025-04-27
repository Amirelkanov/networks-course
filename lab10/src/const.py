from typing import Dict

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
ICMP_DEST_UNREACH = 3

# ICMP codes for destination unreachable (type 3)
ICMP_UNREACH_CODES: Dict[int, str] = {
    0: "Network unreachable",
    1: "Host unreachable",
    2: "Protocol unreachable",
    3: "Port unreachable",
    4: "Fragmentation needed and DF set",
    5: "Source route failed",
    6: "Destination network unknown",
    7: "Destination host unknown",
    8: "Source host isolated",
    9: "Network administratively prohibited",
    10: "Host administratively prohibited",
    11: "Network unreachable for TOS",
    12: "Host unreachable for TOS",
    13: "Communication administratively prohibited",
    14: "Host Precedence Violation",
    15: "Precedence cutoff in effect",
}

BUF_SIZE = 1024
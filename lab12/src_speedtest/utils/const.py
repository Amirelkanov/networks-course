import struct


# Each packet header has the following structure:
# | total_count (uint32) | seq (uint32) | timestamp (double) | payload_len (uint32) |
HEADER_FMT = "!IIdI"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
PAYLOAD_SIZE = 1024

UDP_SOCKET_TIMOUT = 5.0

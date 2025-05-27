import struct

from utils.const import HEADER_FMT


def make_packet(total_count: int, seq: int, ts: float, payload: bytes) -> bytes:
    header = struct.pack(HEADER_FMT, total_count, seq, ts, len(payload))
    return header + payload


def format_speed(speed_bps: float) -> str:
    if speed_bps < 1024:
        return f"{speed_bps:.3f} B/s"
    elif speed_bps < 1024**2:
        return f"{speed_bps / 1024:.3f} KB/s"
    elif speed_bps < 1024**3:
        return f"{speed_bps / (1024 ** 2):.3f} MB/s"
    else:
        return f"{speed_bps / (1024 ** 3):.3f} GB/s"

import struct
import zlib


class Packet:
    # | seqnum ({0, 1}; 1B) | fin flag (1B) | checksum (4B) |
    HEADER_FORMAT = "!BBI"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, seqnum, data=b"", is_fin=False):
        self.seqnum = seqnum
        self.is_fin = is_fin
        self.data = data or b""
        self.checksum = self.calc_checksum()

    def calc_checksum(self):
        buf = struct.pack("!BB", self.seqnum, int(self.is_fin)) + self.data
        return zlib.crc32(buf) & 0xFFFFFFFF

    def is_corrupted(self):
        buf = struct.pack("!BB", self.seqnum, int(self.is_fin)) + self.data
        return (zlib.crc32(buf) & 0xFFFFFFFF) != self.checksum

    def to_bytes(self):
        header = struct.pack(
            self.HEADER_FORMAT, self.seqnum, int(self.is_fin), self.checksum
        )
        return header + self.data

    @classmethod
    def from_bytes(cls, raw_bytes):
        if len(raw_bytes) < cls.HEADER_SIZE:
            raise ValueError("Packet too small")
        seqnum, fin_flag, checksum = struct.unpack(
            cls.HEADER_FORMAT, raw_bytes[: cls.HEADER_SIZE]
        )
        data = raw_bytes[cls.HEADER_SIZE :]

        pkt = cls.__new__(cls)
        pkt.seqnum = seqnum
        pkt.is_fin = bool(fin_flag)
        pkt.data = data
        pkt.checksum = checksum
        return pkt

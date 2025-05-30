from const import INITIAL_CRC, POLY


def crc16(data: bytes) -> int:
    crc = INITIAL_CRC
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ POLY
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def append_crc16(data: bytes) -> bytes:
    crc = crc16(data)
    return data + crc.to_bytes(2)


def check_crc16(packet: bytes) -> bool:
    data, recv_crc = packet[:-2], int.from_bytes(packet[-2:])
    calc_crc = crc16(data)
    return calc_crc == recv_crc

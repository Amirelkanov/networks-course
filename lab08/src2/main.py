def calc_checksum(data: bytes) -> int:
    total = 0
    for i in range(0, len(data), 2):
        word = int.from_bytes(data[i : i + 2], "big")
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


def is_corrupted(data: bytes, checksum: int) -> bool:
    total = checksum
    for i in range(0, len(data), 2):
        word = int.from_bytes(data[i : i + 2], "big")
        total += word
        total = (total & 0xFFFF) + (total >> 16)

    return (total & 0xFFFF) != 0xFFFF

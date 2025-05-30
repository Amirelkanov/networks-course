from typing import Dict, List, Tuple
from main import crc16, append_crc16, check_crc16

"""
Map type for corrupted packets:
* key = packet index
* value = list of (byte_offset, bit_offset)

Example: {0: [(1, 7)]} means that 7th bit of 1st byte of packet 0 will be flipped
"""
type CorruptedMap = Dict[int, List[Tuple[int, int]]]


def split_into_packets(data: bytes, packet_size: int) -> List[bytes]:
    return [data[i : i + packet_size] for i in range(0, len(data), packet_size)]


# Mutate data by bit flipping in specified byte and bit positions
def corrupt_bits(data: bytes, bit_positions: List[Tuple[int, int]]) -> bytes:
    ba = bytearray(data)
    for byte_idx, bit_idx in bit_positions:
        if 0 <= byte_idx < len(ba) and 0 <= bit_idx < 8:
            ba[byte_idx] ^= 1 << bit_idx
    return bytes(ba)


def test_crc16_packets_with_errors(text: str, corrupted_map: CorruptedMap):
    print(
        f"{'=' * 50}\nTesting CRC-16 with packet corruption for following text: \n{text}\n{'=' * 50}\n"
    )
    packets = split_into_packets(text, 5)
    for idx, payload in enumerate(packets):
        # Append CRC to payload
        encoded = append_crc16(payload)
        crc_val = crc16(payload)

        if idx in corrupted_map:  # corrupt the packet if specified in map
            data_part, crc_part = encoded[:-2], encoded[-2:]
            corrupted_data = corrupt_bits(data_part, corrupted_map[idx])
            packet = corrupted_data + crc_part
        else:
            packet = encoded

        ok = check_crc16(packet)

        # Print packet summary
        print(f"Packet {idx}:")
        print(f"\tPayload:\t\t{payload!r}")
        print(f"\tEncoded:\t\t{packet.hex()}")
        print(f"\tExpected CRC:\t\t0x{crc_val:04X}")
        print(f"\tCRC Valid?\t\t{ok}")
        print("-" * 50)

        if idx in corrupted_map:
            assert not ok, f"Packet {idx} was corrupted but CRC check passed."
        else:
            assert ok, f"Packet {idx} is intact but CRC check failed."


if __name__ == "__main__":
    text = b"Hello my name is Amir Elkanov blah blah"
    corrupted_map = {
        1: [(0, 0)],  # flip LSB of first byte in packet 1
        3: [(2, 3), (4, 7)],  # flip two bits in packet 3
    }
    test_crc16_packets_with_errors(text, corrupted_map)

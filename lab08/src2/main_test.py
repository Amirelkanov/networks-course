from main import calc_checksum, is_corrupted


# Good case scenario
def test_simple_data():
    data = b"Hello World"
    checksum = calc_checksum(data)
    assert not is_corrupted(data, checksum)


def test_empty_data():
    data = b""
    checksum = calc_checksum(data)
    assert not is_corrupted(data, checksum)


def test_binary_data_with_odd_length():
    data = b"\x01\x02\x03\x04\x05"
    checksum = calc_checksum(data)
    assert not is_corrupted(data, checksum)


# Bad case scenario
def test_altered_data():
    data = b"Hello World"
    checksum = calc_checksum(data)
    altered_data = b"Hello Wprld"
    assert is_corrupted(altered_data, checksum)


def test_incorrect_checksum():
    data = b"Testing checksum"
    correct_checksum = calc_checksum(data)
    wrong_checksum = (correct_checksum + 1) & 0xFFFF
    assert is_corrupted(data, wrong_checksum)


def test_swapped_last_bytes():
    data = b"\x01\x02\x03\x04"
    checksum = calc_checksum(data)
    altered_data = b"\x01\x02\x04\x03"
    assert is_corrupted(altered_data, checksum)


if __name__ == "__main__":
    test_simple_data()
    test_empty_data()
    test_binary_data_with_odd_length()
    test_altered_data()
    test_incorrect_checksum()
    test_swapped_last_bytes()

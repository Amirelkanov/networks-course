BUF_SIZE = 4096


def chunk_file(file_path, chunk_size):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

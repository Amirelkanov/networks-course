import socket

from const import BUF_SIZE


def run_client(host: str, port: int, message: str):
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(message.encode("utf-8"))

        data = sock.recv(BUF_SIZE)
        print(f"Response from server: {data.decode('utf-8').strip()}")

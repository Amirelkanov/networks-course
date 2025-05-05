import socket

from const import BUF_SIZE


def run_server(host: str, port: int):
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((host, port))
        server_sock.listen()
        print(f"Server started on [{host}]:{port} (IPv6). Waiting for connections...")

        while True:
            conn, addr = server_sock.accept()
            with conn:
                print(f"Client connected {addr}")
                try:
                    while True:
                        data = conn.recv(BUF_SIZE)
                        if not data:
                            break
                        text = data.decode("utf-8")
                        print(f"Received: {text.strip()}")
                        response = text.upper().encode("utf-8")
                        conn.sendall(response)
                except ConnectionResetError:
                    print(f"Client {addr} unexpectedly disconnected")
                print(f"Client {addr} disconnected")

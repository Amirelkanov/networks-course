import argparse
import logging
import socket
from const import BUF_SIZE


def parse_arguments():
    parser = argparse.ArgumentParser(description="Client for lab03")
    parser.add_argument("--server_host", help="Server host", default="localhost")
    parser.add_argument("--server_port", type=int, help="Server port", default=12345)
    parser.add_argument("--filename", help="Filename to request", default="index.html")

    return parser.parse_args()


def send_request(server_host, server_port, filename):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))

    request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}:{server_port}\r\n\r\n"
    client_socket.sendall(request.encode())

    response_data = b""
    while True:
        chunk = client_socket.recv(BUF_SIZE)
        if not chunk:
            break
        response_data += chunk

    client_socket.close()
    process_response(response_data, filename)


def process_response(response_data, filename):
    try:
        header_end = response_data.find(b"\r\n\r\n")
        if header_end == -1:
            logging.error("No headers found in response.")
            return

        headers_raw = response_data[:header_end].decode()
        body = response_data[header_end + 4 :]

        headers = headers_raw.split("\r\n")
        content_type = next(
            (h for h in headers if h.lower().startswith("content-type:")), ""
        )

        if "text/" in content_type:
            text = body.decode(errors="replace")
            logging.info(f"Response for {filename}:\n{headers_raw}\n\n{text}")
        else:
            with open(filename, "wb") as file:
                file.write(body)
            logging.info(
                f"Response for {filename}:\n{headers_raw}\n\nNon-text content saved to {filename}."
            )
    except Exception as e:
        logging.error(f"Failed to process response: {e}")


if __name__ == "__main__":
    args = parse_arguments()

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    send_request(args.server_host, args.server_port, args.filename)

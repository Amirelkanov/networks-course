import socket
import threading
import argparse
import logging
from urllib.parse import urlparse
from const import BUF_SIZE


def parse_arguments():
    parser = argparse.ArgumentParser(description="Proxy Server for Lab04")
    parser.add_argument(
        "--server_port", type=int, default=8888, help="Port to listen on"
    )
    parser.add_argument(
        "--concurrency_level",
        type=int,
        default=1,
        help="Maximum number of concurrent connections",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--log_file", type=str, default="proxy.log", help="Log file name"
    )
    return parser.parse_args()


def init_logger(log_level, log_file):
    logger = logging.getLogger(__name__)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    numeric_level = getattr(logging, log_level.upper(), None)
    if isinstance(numeric_level, int):
        logger.setLevel(numeric_level)
    else:
        logger.setLevel(logging.INFO)
    return logger


def handle_request(connection_socket: socket.socket):
    try:
        request_data = b""
        while True:
            chunk = connection_socket.recv(BUF_SIZE)
            if not chunk:
                logger.debug("Connection closed by client")
                return

            request_data += chunk

            # Check if we received the end of headers
            if b"\r\n\r\n" in request_data:
                break

        header_data, _, body = request_data.partition(b"\r\n\r\n")
        header_lines = header_data.decode("utf-8", errors="replace").split("\r\n")

        if len(header_lines) < 1:
            logger.warning("Malformed request received")
            connection_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        # Parse the request line
        request_line = header_lines[0]
        parts = request_line.split()
        if len(parts) != 3:
            logger.warning(f"Malformed request line: {request_line}")
            connection_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        method, path, version = parts
        logger.debug(f"Received {method} request for {path}")

        content_length = next(
            (
                int(h.split(":", 1)[1].strip())
                for h in header_lines[1:]
                if h.lower().startswith("content-length:")
            ),
            0,
        )
        logger.info(f"Content-Length: {content_length}")

        # Read the rest of the body if needed
        while len(body) < content_length:
            chunk = connection_socket.recv(BUF_SIZE)
            if not chunk:
                logger.warning("Connection closed before receiving complete body")
                break
            body += chunk

        # Parse target URL (e.x. "/www.google.com")
        target = path.lstrip("/")
        if not (target.startswith("http://") or target.startswith("https://")):
            target = "http://" + target

        parsed_url = urlparse(target)
        hostname = parsed_url.hostname
        if not hostname:
            logger.warning(f"Invalid URL: {target}")
            connection_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        port = parsed_url.port if parsed_url.port else 80
        remote_path = parsed_url.path if parsed_url.path else "/"
        if parsed_url.query:
            remote_path += "?" + parsed_url.query

        logger.info(f"Proxying {method} request to {hostname}:{port}{remote_path}")

        # Reconstruct the request for the remote server
        new_request_line = f"{method} {remote_path} {version}\r\n"
        new_headers = []
        host_header_present = False

        for header in header_lines[1:]:
            if ":" not in header:
                continue

            header_name, header_value = header.split(":", 1)
            header_name, header_value = (
                header_name.strip().lower(),
                header_value.strip(),
            )

            if header_name in ["proxy-connection", "connection"]:
                continue

            if header_name == "host":
                host_header_present = True
                new_headers.append(f"Host: {hostname}")
            else:
                new_headers.append(f"{header_name.capitalize()}: {header_value}")

        if not host_header_present:
            new_headers.append(f"Host: {hostname}")
        new_headers.append("Connection: close")

        request_message = new_request_line + "\r\n".join(new_headers) + "\r\n\r\n"
        final_request = request_message.encode() + body

        # Connect to the remote server and send the request
        try:
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.settimeout(10)
            remote_socket.connect((hostname, port))
            remote_socket.sendall(final_request)

            # Send the remote server's response back to the client
            response_data = b""
            response_code = "N/A"
            headers_received = False

            while True:
                remote_data = remote_socket.recv(BUF_SIZE)
                if not remote_data:
                    break

                response_data += remote_data
                connection_socket.sendall(remote_data)

                # Extract response code from the first line if not done yet
                if not headers_received and b"\r\n" in response_data:
                    headers_received = True
                    response_line = response_data.split(b"\r\n")[0].decode(
                        errors="ignore"
                    )
                    status_parts = response_line.split()
                    response_code = status_parts[1] if len(status_parts) >= 2 else "N/A"

            logger.info(
                f"Proxied request: {target} with response code: {response_code}"
            )

        except socket.timeout:
            logger.error(f"Connection to {hostname}:{port} timed out")
            connection_socket.sendall(
                b"HTTP/1.1 504 Gateway Timeout\r\n\r\nGateway Timeout"
            )
        except socket.gaierror:
            logger.error(f"Could not resolve hostname: {hostname}")
            connection_socket.sendall(
                b"HTTP/1.1 502 Bad Gateway\r\n\r\nBad Gateway: Could not resolve hostname"
            )
        except ConnectionRefusedError:
            logger.error(f"Connection refused by {hostname}:{port}")
            connection_socket.sendall(
                b"HTTP/1.1 502 Bad Gateway\r\n\r\nBad Gateway: Connection refused"
            )
        except Exception as e:
            logger.error(f"Error connecting to remote server: {e}", exc_info=True)
            connection_socket.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\nBad Gateway")
        finally:
            try:
                remote_socket.close()
            except:
                pass

    except Exception as e:
        logger.error(f"Error in proxy handling: {e}", exc_info=True)
        try:
            error_response = (
                "HTTP/1.1 500 Internal Server Error\r\n\r\nInternal Server Error"
            )
            connection_socket.sendall(error_response.encode())
        except Exception:
            pass


def client_handler(connection_socket, addr, connection_semaphore):
    try:
        logger.info(f"[{addr[0]}:{addr[1]}] Handling connection...")
        try:
            handle_request(connection_socket)
        except Exception as e:
            logger.error(f"Error handling connection: {e}", exc_info=True)
        finally:
            logger.info(f"[{addr[0]}:{addr[1]}] Connection closed")
            try:
                connection_socket.close()
            except:
                pass
    finally:
        connection_semaphore.release()


def run_server(port: int, concurrency_level: int):
    try:
        connection_semaphore = threading.Semaphore(concurrency_level)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", port))
        server_socket.listen(concurrency_level)
        logger.info(
            f"Proxy server started on port {port} with concurrency level {concurrency_level}"
        )

        while True:
            try:
                connection_socket, addr = server_socket.accept()
                logger.info(f"[{addr[0]}:{addr[1]}] Connection established")

                if connection_semaphore.acquire():
                    client_thread = threading.Thread(
                        target=client_handler,
                        args=(connection_socket, addr, connection_semaphore),
                    )
                    client_thread.daemon = True
                    client_thread.start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}", exc_info=True)
                connection_semaphore.release()
    except KeyboardInterrupt:
        logger.info("Server stopped by user: KeyboardInterrupt")
    except Exception as e:
        logger.critical(f"Server error: {e}", exc_info=True)
    finally:
        try:
            server_socket.close()
            logger.info("Server socket closed")
        except:
            pass


if __name__ == "__main__":
    args = parse_arguments()
    logger = init_logger(args.log_level, args.log_file)

    print(f"Running with arguments: {args}")
    print(f"Logs will be saved to {args.log_file}")

    run_server(args.server_port, args.concurrency_level)

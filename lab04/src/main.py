import socket
import threading
import argparse
import logging
from const import BUF_SIZE
from helpers import (
    build_remote_request,
    extract_target_info,
    parse_http_request,
    relay_response,
)


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
    remote_socket = None

    try:
        # Read the complete request
        request_data = b""
        while True:
            chunk = connection_socket.recv(BUF_SIZE)
            if not chunk:
                logger.debug("Connection closed by client")
                return

            request_data += chunk

            # Check if we've received the end of headers
            if b"\r\n\r\n" in request_data:
                break

        header_lines, method, path, version, body, content_length = parse_http_request(
            request_data
        )

        if not header_lines:
            logger.warning("Malformed request received")
            connection_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        if not method:
            logger.warning(f"Malformed request line")
            connection_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        logger.debug(f"Received {method} request for {path}")
        logger.debug(f"Content-Length: {content_length}")

        # Read the rest of the body if needed for POST requests
        while len(body) < content_length:
            chunk = connection_socket.recv(BUF_SIZE)
            if not chunk:
                logger.warning("Connection closed before receiving complete body")
                break
            body += chunk

        hostname, port, remote_path, target = extract_target_info(path)

        if not hostname:
            logger.warning(f"Invalid URL: {target}")
            connection_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        logger.info(f"Proxying {method} request to {hostname}:{port}{remote_path}")

        final_request = build_remote_request(
            method, remote_path, version, header_lines, hostname, body
        )

        # Connect to the remote server and send the request
        try:
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.settimeout(10)
            remote_socket.connect((hostname, port))
            remote_socket.sendall(final_request)

            response_code = relay_response(remote_socket, connection_socket)

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

    except Exception as e:
        logger.error(f"Error in proxy handling: {e}", exc_info=True)
        try:
            error_response = (
                "HTTP/1.1 500 Internal Server Error\r\n\r\nInternal Server Error"
            )
            connection_socket.sendall(error_response.encode())
        except Exception:
            pass
    finally:
        if remote_socket:
            try:
                remote_socket.close()
            except:
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

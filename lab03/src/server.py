import socket
import threading
import argparse
import logging
from pathlib import Path

from const import DATA_DIR, BUF_SIZE


def parse_arguments():
    parser = argparse.ArgumentParser(description="Server for lab03")
    parser.add_argument(
        "--server_port", type=int, default=12345, help="Port to listen on"
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
    return parser.parse_args()


def get_content_type(file_extension):
    content_types = {
        ".html": "text/html",
        ".htm": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".txt": "text/plain",
        ".json": "application/json",
        ".pdf": "application/pdf",
        ".xml": "application/xml",
        ".svg": "image/svg+xml",
    }
    return content_types.get(file_extension, "application/octet-stream")


def get_response(request: str):
    try:
        request_parts = request.split()
        if len(request_parts) < 2:
            logger.warning("Malformed request received")
            return build_error_response(400, "Bad Request")

        method, path = request_parts[0], request_parts[1]

        if method != "GET":
            return build_error_response(501, "Not Implemented")

        filename = path[1:] if path.startswith("/") else path
        filepath = Path.cwd() / DATA_DIR / filename
        if Path.exists(filepath) and Path.is_file(filepath):
            with open(filepath, "rb") as file:
                content = file.read()
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: {get_content_type(filepath.suffix)}\r\n"
                f"Content-Length: {len(content)}\r\n"
                f"Connection: close\r\n\r\n"
            )
            response = header.encode() + content
            logger.debug(f"File found: {filepath}, size: {len(content)} bytes")
            return response
        else:
            logger.debug(f"File not found: {filepath}")
            return build_error_response(404, "Not Found")
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return build_error_response(500, "Internal Server Error")


def build_error_response(status_code, message):
    content = f"<html><body><h1>{status_code} {message}</h1></body></html>".encode()
    header = (
        f"HTTP/1.1 {status_code} {message}\r\n"
        f"Content-Type: text/html\r\n"
        f"Content-Length: {len(content)}\r\n"
        f"Connection: close\r\n\r\n"
    )
    return header.encode() + content


def handle_request(connection_socket: socket.socket):
    try:
        request = connection_socket.recv(BUF_SIZE).decode("utf-8", errors="replace")
        if not request:
            logger.debug("Empty request received")
            return
        connection_socket.sendall(get_response(request))
    except socket.timeout:
        logger.warning("Request timed out")
    except Exception as e:
        logger.error(f"Error handling request: {e}", exc_info=True)


def client_handler(connection_socket, addr, connection_semaphore):
    try:
        # connection_socket.settimeout(5)
        logger.info(f"[{addr[0]}:{addr[1]}] Handling connection...")

        try:
            handle_request(connection_socket)
            logger.info(
                f"[{addr[0]}:{addr[1]}] Request has been processed. Closing connection..."
            )
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
            f"Server started on port {port} with concurrency level {concurrency_level}"
        )
        logger.info(f"Serving files from directory: {Path.cwd() / DATA_DIR}")

        while True:
            try:
                connection_semaphore.acquire()
                connection_socket, addr = server_socket.accept()
                logger.info(f"[{addr[0]}:{addr[1]}] Connection established")

                client_thread = threading.Thread(
                    target=client_handler,
                    args=(connection_socket, addr, connection_semaphore),
                )
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                logger.error(f"Error accepting connection: {e}", exc_info=True)

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
    logger = logging.getLogger(__name__)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    print(f"Running with arguments: {args}")

    numeric_level = getattr(logging, args.log_level.upper(), None)
    if isinstance(numeric_level, int):
        logger.setLevel(numeric_level)

    run_server(args.server_port, args.concurrency_level)

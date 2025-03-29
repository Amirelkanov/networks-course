import json
import os
import socket
import threading
from const import BUF_SIZE, CACHE_DIR
from helpers import (
    build_remote_request,
    extract_target_info,
    get_blacklist_entries,
    get_cache_paths,
    parse_http_request,
)
from setup import init_logger, parse_arguments


def handle_request(connection_socket: socket.socket):
    remote_socket = None

    try:
        # Read the complete client request
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

        if not header_lines or not method:
            logger.warning("Malformed request received")
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

        blacklist = get_blacklist_entries()
        for blocked in blacklist:
            if blocked.lower() in target.lower():
                logger.warning(f"Blocked request: {target} is blacklisted")
                block_response = (
                    "HTTP/1.1 403 Forbidden\r\n"
                    "Content-Type: text/html\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                    "<html><body><h1>Access Blocked</h1>"
                    "<p>This page is blocked by the proxy server.</p>"
                    "</body></html>"
                )
                connection_socket.sendall(block_response.encode())
                return

        logger.info(f"Proxying {method} request to {hostname}:{port}{remote_path}")

        # For GET requests, check the cache
        cache_meta = {}
        meta_exists = False
        if method.upper() == "GET":
            meta_path, content_path = get_cache_paths(target)
            if os.path.exists(meta_path) and os.path.exists(content_path):
                meta_exists = True
                with open(meta_path, "r") as f:
                    cache_meta = json.load(f)

                # Append conditional GET headers if available
                if "Last-Modified" in cache_meta:
                    header_lines.append(
                        f"If-Modified-Since: {cache_meta['Last-Modified']}"
                    )
                if "Etag" in cache_meta:
                    header_lines.append(f"If-None-Match: {cache_meta['Etag']}")

        final_request = build_remote_request(
            method, remote_path, version, header_lines, hostname, body
        )

        # Connect to the remote server and send the request
        try:
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.settimeout(10)
            remote_socket.connect((hostname, port))
            remote_socket.sendall(final_request)

            response_data = b""
            while True:
                chunk = remote_socket.recv(BUF_SIZE)
                if not chunk:
                    break
                response_data += chunk

            response_lines = response_data.split(b"\r\n")
            if response_lines:
                status_line = response_lines[0].decode(errors="ignore")
                status_parts = status_line.split()
                response_code = status_parts[1] if len(status_parts) >= 2 else "N/A"
            else:
                response_code = "N/A"

            # If we did a conditional GET and got a 304, serve the cached copy
            if response_code == "304" and meta_exists:
                logger.info(f"Serving {target} from cache (304 Not Modified)")
                with open(content_path, "rb") as cache_file:
                    cached_response = cache_file.read()
                connection_socket.sendall(cached_response)
            else:
                # If everything's good, update the cache
                if method.upper() == "GET" and response_code == "200":
                    header_data, _, _ = response_data.partition(b"\r\n\r\n")
                    headers = header_data.decode("utf-8", errors="replace").split(
                        "\r\n"
                    )
                    new_meta = {}
                    for header in headers:
                        if header.lower().startswith("last-modified:"):
                            new_meta["Last-Modified"] = header.split(":", 1)[1].strip()
                        elif header.lower().startswith("etag:"):
                            new_meta["Etag"] = header.split(":", 1)[1].strip()

                    # Save metadata and the full response to cache
                    meta_path, content_path = get_cache_paths(target)
                    with open(meta_path, "w") as meta_file:
                        json.dump(new_meta, meta_file)
                    with open(content_path, "wb") as cache_file:
                        cache_file.write(response_data)
                    logger.info(f"Cached {target}")

                # Send the cached/new response to the client
                connection_socket.sendall(response_data)

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
        os.makedirs(CACHE_DIR, exist_ok=True)

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

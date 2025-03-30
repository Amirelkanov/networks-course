import socket
import sys
import threading
import argparse
import logging
import subprocess

from const import BUF_SIZE


def parse_arguments():
    parser = argparse.ArgumentParser(description="Remote Command Execution Server")
    parser.add_argument("--port", type=int, default=12345, help="Port to listen on")
    parser.add_argument(
        "--concurrency_level",
        type=int,
        default=5,
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


def execute_command(command):
    try:
        encoding = "cp866" if sys.platform.startswith("win") else "utf-8"
        process = subprocess.Popen(
            command,
            shell=True,  # Allow commands like 'calc' or 'notepad'
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding=encoding,
            errors="replace",
        )

        stdout, stderr = process.communicate(timeout=30)
        return_code = process.returncode

        response = f"Command: {command}\n"
        response += f"Return Code: {return_code}\n\n"
        if stdout:
            response += f"--- STDOUT ---\n{stdout}\n"
        if stderr:
            response += f"--- STDERR ---\n{stderr}\n"

        return response
    except subprocess.TimeoutExpired:
        process.kill()
        return f"Command timed out after 30 seconds: {command}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def handle_client(client_socket, addr, connection_semaphore):
    try:
        logger.info(f"[{addr[0]}:{addr[1]}] Connection established")

        data = client_socket.recv(BUF_SIZE).decode("utf-8", errors="replace")
        if not data:
            logger.warning(f"[{addr[0]}:{addr[1]}] Empty command received")
            return

        command = data.strip()
        logger.info(f"[{addr[0]}:{addr[1]}] Received command: {command}")

        result = execute_command(command)
        client_socket.sendall(result.encode("utf-8", errors="replace"))

        logger.info(f"[{addr[0]}:{addr[1]}] Command executed and result sent")
    except Exception as e:
        logger.error(f"[{addr[0]}:{addr[1]}] Error handling client: {e}", exc_info=True)
    finally:
        client_socket.close()
        logger.info(f"[{addr[0]}:{addr[1]}] Connection closed")
        connection_semaphore.release()


def run_server(port, concurrency_level):
    try:
        connection_semaphore = threading.Semaphore(concurrency_level)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind(("", port))
        server_socket.listen(concurrency_level)

        logger.info(
            f"Server started on port {port} with concurrency level {concurrency_level}"
        )
        logger.info("Waiting for incoming connections...")

        while True:
            try:
                client_socket, addr = server_socket.accept()

                if connection_semaphore.acquire():
                    client_thread = threading.Thread(
                        target=handle_client,
                        args=(client_socket, addr, connection_semaphore),
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
    print(f"Running with arguments: {args}")

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    run_server(args.port, args.concurrency_level)

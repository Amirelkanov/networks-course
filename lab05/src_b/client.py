import socket
import argparse
import logging
import sys

from const import BUF_SIZE


def parse_arguments():
    parser = argparse.ArgumentParser(description="Remote Command Execution Client")
    parser.add_argument(
        "--host", type=str, default="localhost", help="Server hostname or IP address"
    )
    parser.add_argument("--port", type=int, default=12345, help="Server port")
    parser.add_argument("--command", type=str, help="Command to execute on the server")
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    return parser.parse_args()


def send_command(host, port, command, logger):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        logger.info(f"Connecting to {host}:{port}")
        client_socket.connect((host, port))

        logger.info(f"Sending command: {command}")
        client_socket.sendall(command.encode("utf-8"))

        logger.debug("Waiting for server response...")
        result = b""

        while True:
            chunk = client_socket.recv(BUF_SIZE)
            if not chunk:
                break
            result += chunk

        return result.decode("utf-8", errors="replace")

    except ConnectionRefusedError:
        logger.error(
            f"Connection refused. Make sure the server is running at {host}:{port}"
        )
        return "Connection refused. Make sure the server is running."
    except socket.timeout:
        logger.error("Connection timed out. The server might be busy or unreachable.")
        return "Connection timed out. The server might be busy or unreachable."
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"
    finally:
        client_socket.close()


def interactive_mode(host, port, logger):
    print(f"=== Remote Command Execution Client ===")
    print(f"Connected to {host}:{port}")
    print("Type 'exit' or 'quit' to terminate the session")
    print("=========================================")

    while True:
        try:
            command = input(":> ")

            if command.lower() in ("exit", "quit"):
                print("Exiting...")
                break

            if not command.strip():  # Skip empty commands
                continue

            result = send_command(host, port, command, logger)
            print("\n=== Command Result ===")
            print(result)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    args = parse_arguments()
    print(f"Running with arguments: {args}")

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.interactive:
        interactive_mode(args.host, args.port, logger)
    elif args.command:
        result = send_command(args.host, args.port, args.command, logger)
        print(result)
    else:
        print(
            "Error: Either provide a command with --command or use --interactive mode"
        )
        sys.exit(1)

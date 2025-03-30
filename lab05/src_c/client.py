import socket
import argparse
import logging
import time
from const import BUF_SIZE


def parse_arguments():
    parser = argparse.ArgumentParser(description="UDP Time Broadcasting Client")
    parser.add_argument("--port", type=int, default=12345, help="Port to listen on")
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    return parser.parse_args()


def run_time_client(port, logger):
    try:
        client_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.bind(("", port))
        last_received_time = None

        logger.info(f"UDP Time Client started")
        logger.info("Press Ctrl+C to stop the client")
        print("\n--- Received Time Broadcasts ---")

        # Receive and display time broadcasts
        while True:
            try:
                data, addr = client_socket.recvfrom(BUF_SIZE)
                received_time = data.decode("utf-8")

                if received_time != last_received_time:
                    print(f"Server Time: {received_time} (from {addr[0]}:{addr[1]})")
                    last_received_time = received_time
                    logger.debug(
                        f"Received time: {received_time} from {addr[0]}:{addr[1]}"
                    )

            except Exception as e:
                logger.error(f"Error receiving time: {e}", exc_info=True)

    except KeyboardInterrupt:
        logger.info("Client stopped by user: KeyboardInterrupt")
    except Exception as e:
        logger.critical(f"Client error: {e}", exc_info=True)
    finally:
        try:
            client_socket.close()
            logger.info("Client socket closed")
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

    run_time_client(args.port, logger)

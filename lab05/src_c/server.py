import socket
import time
import datetime
import argparse
import logging


def parse_arguments():
    parser = argparse.ArgumentParser(description="UDP Time Broadcasting Server")
    parser.add_argument("--port", type=int, default=12345, help="Broadcast port")
    parser.add_argument(
        "--format", type=str, default="%Y-%m-%d %H:%M:%S", help="Time format"
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    return parser.parse_args()


def run_time_server(port, time_format):
    try:
        server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        logger.info(f"UDP Time Broadcasting Server started")
        logger.info(f"Time format: {time_format}")
        logger.info("Press Ctrl+C to stop the server")

        # Broadcast time every second
        while True:
            try:
                current_time = datetime.datetime.now().strftime(time_format)
                server_socket.sendto(
                    current_time.encode("utf-8"), ("<broadcast>", port)
                )

                logger.debug(f"Broadcasted time: {current_time}")
            except Exception as e:
                logger.error(f"Error broadcasting time: {e}", exc_info=True)
            finally:
                time.sleep(1)

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

    run_time_server(args.port, args.format)

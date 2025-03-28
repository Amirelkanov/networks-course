import argparse
import logging


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

import argparse
import sys

from client import run_client
from server import run_server


def add_server_subparser(subparsers):
    srv_parser = subparsers.add_parser("server", help="Start the echo server")
    srv_parser.add_argument(
        "--host",
        type=str,
        default="::",
        help="IPv6 address of the server",
    )
    srv_parser.add_argument(
        "--port",
        type=int,
        default=12345,
        help="TCP port to listen on",
    )


def add_client_subparser(subparsers):
    cli_parser = subparsers.add_parser("client", help="Start the echo client")
    cli_parser.add_argument("message", type=str, help="Text message to send")
    cli_parser.add_argument(
        "--host",
        type=str,
        default="::1",
        help="IPv6 address of the server to connect to",
    )
    cli_parser.add_argument(
        "--port", type=int, default=12345, help="TCP port of the server to connect to"
    )


def parse_arguments(parser):
    subparsers = parser.add_subparsers(
        dest="role", required=True, help="Role: server or client"
    )
    add_server_subparser(subparsers)
    add_client_subparser(subparsers)

    return parser.parse_args()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Echo server/client using IPv6")
    args = parse_arguments(parser)

    if args.role == "server":
        run_server(args.host, args.port)
    elif args.role == "client":
        run_client(args.host, args.port, args.message)
    else:
        parser.print_help()
        sys.exit(1)

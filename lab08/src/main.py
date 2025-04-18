import argparse
import socket
import sys

from RDT.receiver import Receiver
from RDT.sender import Sender
from RDT.unreliable_chan import UnreliableChannel


def add_server_subparser(subparsers):
    server_parser = subparsers.add_parser("server", help="Run as server")
    server_parser.add_argument(
        "--port", type=int, required=True, help="Port to listen on"
    )
    server_parser.add_argument(
        "--outfile", type=str, required=True, help="Path to save received file"
    )
    server_parser.add_argument(
        "--loss", type=float, default=0.3, help="Loss probability [0.0-1.0]"
    )


def add_client_subparser(subparsers):
    client_parser = subparsers.add_parser("client", help="Run as client")

    client_parser.add_argument("--port", type=int, required=True, help="Server port")
    client_parser.add_argument("--file", type=str, required=True, help="File to send")

    client_parser.add_argument(
        "--server-ip", type=str, default="localhost", help="Server IP address"
    )
    client_parser.add_argument(
        "--chunk-size", type=int, default=1024, help="Chunk size in bytes"
    )
    client_parser.add_argument(
        "--timeout", type=float, default=1.0, help="Timeout in seconds"
    )
    client_parser.add_argument(
        "--loss", type=float, default=0.3, help="Loss probability [0.0-1.0]"
    )


def parse_arguments(parser):
    subparsers = parser.add_subparsers(dest="role", required=True)

    add_server_subparser(subparsers)
    add_client_subparser(subparsers)

    args = parser.parse_args()

    if args.loss < 0 or args.loss > 1:
        raise ValueError("Loss probability must be between 0 and 1")

    return args


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stop-and-Wait Protocol")
    args = parse_arguments(parser)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if args.role == "server":

        sock.bind(("", args.port))
        channel = UnreliableChannel(sock, loss_prob=args.loss)
        receiver = Receiver(channel, args.outfile)
        receiver.start()
    elif args.role == "client":
        channel = UnreliableChannel(sock, loss_prob=args.loss)
        server_addr = (args.server_ip, args.port)
        sender = Sender(channel, server_addr, timeout=args.timeout)
        sender.send_file(args.file, args.chunk_size)
    else:
        parser.print_help()
        sys.exit(1)

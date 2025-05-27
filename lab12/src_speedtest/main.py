import argparse

from app.client import Client
from app.server import Server
from utils.types import Protocol

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Network: measuring speed and loss over TCP/UDP"
    )
    parser.add_argument(
        "--mode",
        choices=["client", "server"],
        required=True,
        help="mode: client/server",
    )
    parser.add_argument(
        "--protocol",
        type=Protocol,
        choices=[Protocol.TCP, Protocol.UDP],
        required=True,
        help="protocol: tcp/udp",
    )
    args = parser.parse_args()

    app = (
        Client(protocol=args.protocol)
        if args.mode == "client"
        else Server(protocol=args.protocol)
    )
    app.mainloop()

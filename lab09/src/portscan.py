import socket
import argparse
from enum import Enum
from typing import List, Tuple


class PortState(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    TIMEOUT = "TIMEOUT"
    OTHER = "OTHER"


def parse_arguments():
    parser = argparse.ArgumentParser(description="TCP port scanner")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Target hostname or IP address"
    )
    parser.add_argument(
        "-s", "--start", type=int, help="First port to scan (inclusive)"
    )
    parser.add_argument("-e", "--end", type=int, help="Last port to scan (exclusive)")
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=1.0,
        help="Connection timeout in seconds",
    )
    return parser.parse_args()


def scan_ports(
    host: str, start: int, end: int, timeout: float
) -> List[Tuple[int, PortState]]:
    results: List[Tuple[int, PortState]] = []

    for port in range(start, end):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            results.append((port, PortState.OPEN))
        except socket.timeout:
            results.append((port, PortState.TIMEOUT))
        except ConnectionRefusedError:
            results.append((port, PortState.CLOSED))
        except Exception:
            results.append((port, PortState.OTHER))
        finally:
            sock.close()

    return results


if __name__ == "__main__":
    args = parse_arguments()
    ports_status = scan_ports(args.host, args.start, args.end, args.timeout)
    open_ports = [port for port, state in ports_status if state == PortState.OPEN]
    if open_ports:
        print(
            f"{len(open_ports)} open ports on {args.host} in range [{args.start}, {args.end}) were found:\n{', '.join(map(str, open_ports))}"
        )
    else:
        print(
            f"All ports in range [{args.start}, {args.end}) are closed on {args.host}"
        )

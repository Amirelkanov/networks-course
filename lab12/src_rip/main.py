import threading
import socket
import json
import argparse
import time
from typing import Dict

from const import BUF_SIZE, INFINITY, HOST
from network_types import IP, NetworkMessageType

PRINT_LOCK = threading.Lock()


class Router(threading.Thread):
    def __init__(
        self,
        ip: IP,
        port: int,
        neighbour_costs: Dict[IP, int],
        neighbour_ports: Dict[IP, int],
        all_ips: list[IP],
    ):
        super().__init__()
        self.ip = ip
        self.port = port

        self.neighbour_costs = neighbour_costs  # neighbour_ip -> costs
        self.neighbour_ports = neighbour_ports  # neighbour_ip -> port

        self.all_ips = all_ips

        self.dv: Dict[IP, int] = {  # distance vector: dest_ip -> cost
            dest: (0 if dest == self.ip else self.neighbour_costs.get(dest, INFINITY))
            for dest in all_ips
        }
        self.next_hops: Dict[IP, IP] = {  # dest_ip -> next_hop_ip
            dest: (
                self.ip
                if dest == self.ip
                else (dest if dest in self.neighbour_costs else None)
            )
            for dest in all_ips
        }

        # Store last received DV from each neighbour
        self.neighbour_dvs = {}  # neighbour_id -> their DV dict
        self.step = 0
        self.running = True

        # UDP socket for communication
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((HOST, self.port))
        self.sock.settimeout(1)

    # Broadcast current DV to all neighbours
    def broadcast(self):
        with PRINT_LOCK:
            self.step += 1
            print(f"Simulation step {self.step} of router {self.ip}")
            self.print_table()

        msg = {
            "type": NetworkMessageType.DV.value,
            "src": self.ip,
            "dv": {dest: cost for dest, cost in self.dv.items() if cost < INFINITY},
        }

        for nbr_ip, _ in self.neighbour_costs.items():
            nbr_port = self.neighbour_ports[nbr_ip]
            self.sock.sendto(json.dumps(msg).encode(), (HOST, nbr_port))

    def print_table(self):
        print(
            f"{'[Source IP]':<16}{'[Destination IP]':<18}{'[Next Hop]':<16}{'[Metric]':<8}"
        )
        for dest in sorted(self.all_ips):
            cost = self.dv[dest]
            if cost == INFINITY:
                metric = "∞"
                nh = "-"
            else:
                metric = str(int(cost))
                nh = self.next_hops[dest]
            if self.ip != dest:
                print(f"{self.ip:<16}{dest:<18}{nh:<16}{metric:<8}")
        print()

    def run(self):
        # Initial advertisement
        self.broadcast()
        while self.running:
            try:
                data, _ = self.sock.recvfrom(BUF_SIZE)
            except socket.timeout:
                continue
            try:
                msg = json.loads(data.decode())
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            if msg_type == NetworkMessageType.STOP.value:
                self.running = False
                break

            elif msg_type == NetworkMessageType.DV.value:
                neighbour_id, neighbour_dv = msg["src"], msg.get("dv", {})
                updated = False

                self.neighbour_dvs[neighbour_id] = neighbour_dv

                # Recompute distance vector according to Bellman-Ford algorithm
                for dest in self.all_ips:
                    if dest == self.ip:
                        continue

                    best_cost = self.neighbour_costs.get(dest, INFINITY)
                    best_nhop = dest if dest in self.neighbour_costs else None

                    for nbr, cost_to_nbr in self.neighbour_costs.items():
                        nbr_dv = self.neighbour_dvs.get(nbr)
                        if nbr_dv is None:
                            continue
                        cost_via = cost_to_nbr + nbr_dv.get(dest, INFINITY)
                        if cost_via < best_cost:
                            best_cost = cost_via
                            best_nhop = nbr

                    if best_cost != self.dv.get(dest, INFINITY):
                        self.dv[dest] = best_cost
                        self.next_hops[dest] = best_nhop
                        updated = True

                # If we improved any route, notify neighbours about it
                if updated:
                    self.broadcast()

        # We can get into this branch only and only if the router received a STOP message
        # so we print the final state of the routing table
        with PRINT_LOCK:
            print(f"Final state of router {self.ip} table:")
            self.print_table()
        self.sock.close()


def load_config(path):
    """
    Loads the configuration from a JSON file with following format:
        {"routers": [
            {
                "ip": "<ip_1>",
                "port": <port_1>,
                "neighbours": ["<ip_i>", "<ip_j>", ...]
            },
            ...
        ]}
    """
    with open(path, "r") as f:
        data = json.load(f)

    routers_cfg = data.get("routers", [])
    ip_to_port = {r["ip"]: r["port"] for r in routers_cfg}
    all_ips = list(ip_to_port.keys())

    configs = []
    for r in routers_cfg:
        ip, port = r["ip"], r["port"]
        neighbour_costs = {nbr_ip: 1 for nbr_ip in r.get("neighbours", [])}
        configs.append((ip, port, neighbour_costs, ip_to_port, all_ips))
    return configs


def parse_argumets():
    parser = argparse.ArgumentParser(description="RIP protocol emulator")
    parser.add_argument(
        "-c",
        "--config",
        default="src_rip/assets/topology.json",
        help="Path to JSON config file",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=10,
        help="Simulation time in seconds",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_argumets()
    configs = load_config(args.config)

    # Creating and starting routers
    routers = []
    for ip, port, neighbour_costs, neighbour_ports, all_ips in configs:
        r = Router(ip, port, neighbour_costs, neighbour_ports, all_ips)
        routers.append(r)
        r.start()

    time.sleep(args.time)
    print("=" * 80)
    print()
    print("RIP simulation finished, sending STOP messages and getting final states...")
    print()
    print("=" * 80)

    stopper = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    stop_msg = {"type": NetworkMessageType.STOP.value}
    for _, port, _, _, _ in configs:
        stopper.sendto(json.dumps(stop_msg).encode(), (HOST, port))
    stopper.close()

    # thread cleanup
    for r in routers:
        r.join()

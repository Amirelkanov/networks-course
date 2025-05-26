from enum import Enum
import threading
import queue
import time
from typing import Dict, Tuple

INFINITY = float("inf")


class NetworkMessageType(Enum):
    DV = "DV"  # Distance Vector message
    STOP = "STOP"  # Stop message to terminate node threads


type NetworkMessage = Tuple[NetworkMessageType, int, Dict[int, float]]


class Node(threading.Thread):
    def __init__(self, node_id: int, neighbours: Dict[int, float], num_nodes: int):
        super().__init__()
        self.id = node_id
        self.num_nodes = num_nodes
        self.running = True

        self.queue: queue.Queue[NetworkMessage] = queue.Queue()

        self.neighbours = neighbours  # neighbour_id -> link cost
        self.dv: Dict[int, float] = {  # distance vector: dest_id -> cost
            dest: (0 if dest == self.id else self.neighbours.get(dest, INFINITY))
            for dest in range(self.num_nodes)
        }

        # Store last received DV from each neighbour
        self.neighbour_dvs = {}  # neighbour_id -> their DV dict
        self.lock = threading.Lock()

    def send_to_neighbour(self, neighbour_id, message):
        nodes[neighbour_id].queue.put(message)

    # Broadcast current DV to all neighbours
    def broadcast(self):
        with self.lock:
            message = (NetworkMessageType.DV, self.id, self.dv.copy())
        for nbr in self.neighbours:
            self.send_to_neighbour(nbr, message)

    def update_link_cost(self, neighbour_id, new_cost):
        with self.lock:
            self.neighbours[neighbour_id] = new_cost
            self.dv[neighbour_id] = new_cost

        self.broadcast()  # tell about update to neighbours

    def run(self):
        # Initial advertisement
        self.broadcast()
        while self.running:
            try:
                msg = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            msg_type, src, data = msg

            if msg_type is NetworkMessageType.STOP:
                self.running = False
                break

            elif msg_type is NetworkMessageType.DV:
                neighbour_id, neighbour_dv = src, data
                updated = False
                with self.lock:
                    self.neighbour_dvs[neighbour_id] = neighbour_dv

                    # Recompute distance vector according to Bellman-Ford algorithm
                    for dest in range(self.num_nodes):
                        if dest == self.id:
                            continue

                        best = self.neighbours.get(dest, INFINITY)
                        for nbr, cost_to_nbr in self.neighbours.items():
                            nbr_dv = self.neighbour_dvs.get(nbr)
                            if nbr_dv is None:
                                continue
                            best = min(best, cost_to_nbr + nbr_dv.get(dest, INFINITY))

                        if best != self.dv.get(dest, INFINITY):
                            self.dv[dest] = best
                            updated = True

                # If we improved any route, notify neighbours about it
                if updated:
                    self.broadcast()

    def stop(self):
        stop_msg = (NetworkMessageType.STOP, None, None)
        self.queue.put(stop_msg)


def change_link_cost_for_both(u, v, cost):
    # Both endpoints must update their local view of the link
    nodes[u].update_link_cost(v, cost)
    nodes[v].update_link_cost(u, cost)


def print_routing_tables():
    for rid in sorted(nodes):
        print(f"Node {rid}: {nodes[rid].dv}")
    print()


if __name__ == "__main__":
    G = {
        0: {1: 1, 2: 3, 3: 7},
        1: {0: 1, 2: 1},
        2: {1: 1, 0: 3, 3: 2},
        3: {0: 7, 2: 2},
    }
    num_nodes = len(G)

    global nodes
    nodes = {}
    for rid, neighs in G.items():
        nodes[rid] = Node(rid, neighs.copy(), num_nodes)

    # Start all node threads
    for r in nodes.values():
        r.start()

    time.sleep(2)  # For convergence
    print("Initial routing tables:")
    print_routing_tables()

    change_link_cost_for_both(1, 2, 5)

    time.sleep(2)  # For convergence
    print("1-2 link updated routing tables:")
    print_routing_tables()

    change_link_cost_for_both(0, 3, 1)

    time.sleep(2)  # For convergence
    print("0-3 link updated routing tables:")
    print_routing_tables()

    # Cleanup
    for r in nodes.values():
        r.stop()
    for r in nodes.values():
        r.join()

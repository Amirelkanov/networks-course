import socket
from RDT.helpers import BUF_SIZE, chunk_file
from RDT.packet import Packet


class Sender:
    def __init__(self, channel, dest_addr, timeout=1.0):
        self.channel = channel
        self.dest_addr = dest_addr
        self.timeout = timeout
        self.seqnum = 0

    def send(self, data, is_fin=False):
        pkt = Packet(self.seqnum, data, is_fin)
        while True:
            try:
                self.channel.sendto(pkt.to_bytes(), self.dest_addr)

                # Wait for ACK
                self.channel.sock.settimeout(self.timeout)
                raw, _ = self.channel.sock.recvfrom(BUF_SIZE)
                ack = Packet.from_bytes(raw)
                if (
                    not ack.is_corrupted()
                    and ack.seqnum == self.seqnum
                    and ack.is_fin == is_fin
                ):
                    self.seqnum ^= 1
                    return
                else:
                    print(
                        f"[Sender] Received invalid ACK (seq={ack.seqnum}, fin={ack.is_fin}), retransmitting"
                    )
            except socket.timeout:
                print(
                    f"[Sender] Timeout waiting for ACK seq {self.seqnum}, retransmitting"
                )

    def send_file(self, file_path, chunk_size=1024):
        for chunk in chunk_file(file_path, chunk_size):
            print(f"[Sender] Sending chunk seq {self.seqnum}, size {len(chunk)} bytes")
            self.send(chunk, is_fin=False)

        print("[Sender] Sending FIN")
        self.send(b"", is_fin=True)
        print("[Sender] File transfer complete")

from RDT.helpers import BUF_SIZE
from RDT.packet import Packet


class Receiver:
    def __init__(self, channel, save_path):
        self.channel = channel
        self.save_path = save_path
        self.expected_seq = 0
        self.last_ack_seq = 1  # opposite of expected
        self.file = open(self.save_path, "wb")

    def start(self):
        print("[Receiver] Waiting for data...")
        while True:
            raw, addr = self.channel.sock.recvfrom(BUF_SIZE)
            try:
                pkt = Packet.from_bytes(raw)
            except ValueError:
                print("[Receiver] Received malformed packet, ignoring")
                continue
            if not pkt.is_corrupted() and pkt.seqnum == self.expected_seq:
                if pkt.is_fin:
                    ack = Packet(self.expected_seq, b"", is_fin=True)
                    self.channel.sendto(ack.to_bytes(), addr)
                    print("[Receiver] Received FIN, closing connection")
                    break

                # Write data and send ACK
                self.file.write(pkt.data)
                ack = Packet(self.expected_seq, b"", is_fin=False)
                self.channel.sendto(ack.to_bytes(), addr)
                print(f"[Receiver] Received seq {pkt.seqnum}, delivered, sent ACK")
                self.last_ack_seq = self.expected_seq
                self.expected_seq ^= 1
            else:
                # Corrupted or unexpected seq, resend last ACK
                ack = Packet(self.last_ack_seq, b"", is_fin=False)
                self.channel.sendto(ack.to_bytes(), addr)
                print(
                    f"[Receiver] Packet corrupted or out-of-order, resent ACK seq {self.last_ack_seq}"
                )
        self.file.close()
        print("[Receiver] File saved to", self.save_path)

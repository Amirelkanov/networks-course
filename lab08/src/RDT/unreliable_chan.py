import random


class UnreliableChannel:
    def __init__(self, sock, loss_prob=0.3):
        self.sock = sock
        self.loss_prob = loss_prob

    def sendto(self, data, addr):
        if random.random() > self.loss_prob:
            self.sock.sendto(data, addr)
        else:
            print(f'[Channel] Packet to {addr} lost')
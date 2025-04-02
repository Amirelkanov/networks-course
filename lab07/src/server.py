import random
import socket
from const import BUF_SIZE


def main():
    serverPort = 12345
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind(("", serverPort))
    print("UDP Ping Server is running on port", serverPort)

    while True:
        message, clientAddress = serverSocket.recvfrom(BUF_SIZE)
        print("Received message from", clientAddress)

        if random.random() < 0.2:
            print("Simulating packet loss. Packet from", clientAddress, "dropped.")
            continue

        modifiedMessage = message.upper()
        serverSocket.sendto(modifiedMessage, clientAddress)
        print("Sent reply to", clientAddress)


if __name__ == "__main__":
    main()

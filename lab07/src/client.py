import socket
import time
from const import BUF_SIZE


def main():
    serverName, serverPort = "localhost", 12345
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.settimeout(1)

    rtts = []
    total_packets, received_packets = 10, 0

    try:
        serverIP = socket.gethostbyname(serverName)
    except socket.gaierror:
        serverIP = serverName
    print(f"Pinging {serverName} [{serverIP}] with {total_packets} packets:")

    for seq in range(1, total_packets + 1):
        send_time = time.time()
        message = f"Ping {send_time} {seq}"
        try:
            clientSocket.sendto(message.encode(), (serverName, serverPort))
            modifiedMessage, _ = clientSocket.recvfrom(BUF_SIZE)

            rtt = (time.time() - send_time) * 1000
            rtts.append(rtt)
            received_packets += 1

            print(f"Reply from {serverName}: seq={seq} time={rtt:.2f} ms")
            # if modifiedMessage:
            #    print(modifiedMessage.decode())
        except socket.timeout:
            print(f"Request timed out for seq={seq}")

    lost_packets = total_packets - received_packets
    packet_loss = (lost_packets / total_packets) * 100
    if rtts:
        min_rtt, max_rtt, avg_rtt = min(rtts), max(rtts), sum(rtts) / len(rtts)
    else:
        min_rtt = max_rtt = avg_rtt = 0

    print(f"\nPing statistics for {serverIP}:")
    print(
        f"\tPackets: Sent = {total_packets}, Received = {received_packets}, Lost = {lost_packets} ({packet_loss:.1f}% loss)"
    )
    print("Approximate round trip times in milliseconds:")
    print(
        f"\tMinimum = {min_rtt:.2f}ms, Maximum = {max_rtt:.2f}ms, Average = {avg_rtt:.2f}ms"
    )


if __name__ == "__main__":
    main()

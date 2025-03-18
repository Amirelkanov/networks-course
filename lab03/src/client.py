import argparse
import socket

BUF_SIZE = 8192

def parse_arguments():
    parser = argparse.ArgumentParser(description='Client for lab03')
    parser.add_argument('--server_host', help='Server host', default='localhost')
    parser.add_argument('--server_port', type=int, help='Server port', default=12345)
    parser.add_argument('--filename', help='Filename to request', default='index.html')
    
    return parser.parse_args()


def send_request(server_host, server_port, filename):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))

    request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}:{server_port}\r\n\r\n"
    client_socket.sendall(request.encode())

    response = client_socket.recv(BUF_SIZE).decode()
    print(response)

    client_socket.close()

if __name__ == '__main__':
    args = parse_arguments()
    send_request(args.server_host, args.server_port, args.filename)

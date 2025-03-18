from pathlib import Path
import socket
import argparse
import logging
from queue import Queue

DATA_DIR = "data"
BUF_SIZE = 8192

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Server for lab03')
    parser.add_argument('--server_port', type=int, default=12345, help='Port to listen on')
    parser.add_argument('--concurrency_level', type=int, default=1, help='Maximum number of concurrent connections')
    parser.add_argument('--log_level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level')
    return parser.parse_args()

def get_content_type(file_extension):
    content_types = {
        '.html': 'text/html',
        '.htm': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.txt': 'text/plain',
    }
    return content_types.get(file_extension, 'application/octet-stream')


def get_response(request: str):
    filename = request.split()[1][1:]
    filepath = Path.cwd() / DATA_DIR / filename
    if Path.exists(filepath) and Path.is_file(filepath):
        with open(filepath, 'rb') as file:
            content = file.read()
        header = f"HTTP/1.1 200 OK\r\nContent-Type: {get_content_type(filepath.suffix)}\r\nContent-Length: {len(content)}\r\n\r\n"
        response = header.encode() + content
        logger.debug(f"File found: {filepath}, size: {len(content)} bytes")
    else:
        header = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: 0\r\n\r\n"
        response = header.encode()
        logger.warning(f"File not found: {filepath}")
    return response
    
def handle_request(connection_socket: socket):
    try:
        request = connection_socket.recv(BUF_SIZE).decode('utf-8', errors='replace')
        if not request:
            logger.debug("Empty request received")
            return
            
        request_parts = request.split()
        if len(request_parts) < 2:
            logger.warning("Malformed request received")
            return
            
        addr = connection_socket.getpeername()
        logger.info(f"[{addr[0]}:{addr[1]}] Request: {request_parts[0]} {request_parts[1]}")
        
        connection_socket.sendall(get_response(request))
    except Exception as e:
        logger.error(f"Error handling request: {e}", exc_info=True)

def run_server(port: int, concurrency_level: int):
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(('localhost', port))
        serverSocket.listen(concurrency_level)
        
        logger.info(f"Server started on port: {port}")
        logger.info(f"Concurrency level: {concurrency_level}")

        while True:
            logger.debug("Waiting for connection...")
            connectionSocket, addr = serverSocket.accept()
            logger.info(f"Established connection with {addr[0]}:{addr[1]}")
            handle_request(connectionSocket)
            logger.info(f"[{addr[0]}:{addr[1]}] Connection closed")
            connectionSocket.close()
    except Exception as e:
        logger.critical(f"Server error: {e}", exc_info=True)
    finally:
        serverSocket.close()
        logger.info("Server socket closed")

if __name__ == "__main__":
    args = parse_arguments()
    
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if isinstance(numeric_level, int):
        logger.setLevel(numeric_level)
    
    run_server(args.server_port, args.concurrency_level)
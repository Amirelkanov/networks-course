import pygame
import socket
import json
from const import UDP_IP, UDP_PORT, WIDTH, HEIGHT, BG_COLOR, BUF_SIZE


def initialize_pygame():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Server")
    screen.fill(BG_COLOR)
    pygame.display.flip()
    return screen


def create_udp_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)
    return sock


def process_message(screen, msg):
    if msg.get("type") == "draw":
        pygame.draw.circle(
            screen,
            tuple(msg.get("color", ())),
            tuple(msg.get("pos", ())),
            msg.get("radius", 0),
        )
    elif msg.get("type") == "erase":
        pos = msg.get("pos", (0, 0))
        side = msg.get("side", 0)
        rect = (pos[0] - side // 2, pos[1] - side // 2, side, side)
        pygame.draw.rect(screen, BG_COLOR, rect)


def run_server():
    screen = initialize_pygame()
    sock = create_udp_socket()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        try:
            data, _ = sock.recvfrom(BUF_SIZE)
            message = json.loads(data.decode())
            process_message(screen, message)
            pygame.display.update()
        except BlockingIOError:
            continue

    pygame.quit()


if __name__ == "__main__":
    run_server()

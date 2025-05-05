import pygame
import socket
import json
from const import (
    SERVER_IP,
    UDP_PORT,
    WIDTH,
    HEIGHT,
    DRAW_RADIUS,
    DRAW_COLOR,
    ERASE_SIZE,
    BG_COLOR,
)


def send_msg(sock, msg):
    sock.sendto(json.dumps(msg).encode(), (SERVER_IP, UDP_PORT))


def draw_cursor(surface, pos, erase_mode):
    if erase_mode:
        rect = pygame.Rect(
            pos[0] - ERASE_SIZE // 2, pos[1] - ERASE_SIZE // 2, ERASE_SIZE, ERASE_SIZE
        )
        pygame.draw.rect(surface, BG_COLOR, rect)
        pygame.draw.rect(surface, DRAW_COLOR, rect, 1)
    else:
        temp_surface = pygame.Surface(
            (DRAW_RADIUS * 2, DRAW_RADIUS * 2), pygame.SRCALPHA
        )
        semi_transparent_color = (DRAW_COLOR[0], DRAW_COLOR[1], DRAW_COLOR[2], 128)
        pygame.draw.circle(
            temp_surface,
            semi_transparent_color,
            (DRAW_RADIUS, DRAW_RADIUS),
            DRAW_RADIUS,
        )
        pygame.draw.circle(
            temp_surface, DRAW_COLOR, (DRAW_RADIUS, DRAW_RADIUS), DRAW_RADIUS, 1
        )
        surface.blit(temp_surface, (pos[0] - DRAW_RADIUS, pos[1] - DRAW_RADIUS))


def handle_mouse_motion(event, drawing, erase_mode, canvas, sock):
    if drawing:
        try:
            pos = event.pos
        except AttributeError:
            pos = pygame.mouse.get_pos()
        if erase_mode:
            pygame.draw.rect(
                canvas,
                BG_COLOR,
                (
                    pos[0] - ERASE_SIZE // 2,
                    pos[1] - ERASE_SIZE // 2,
                    ERASE_SIZE,
                    ERASE_SIZE,
                ),
            )
            msg = {"type": "erase", "pos": pos, "side": ERASE_SIZE}
        else:
            pygame.draw.circle(canvas, DRAW_COLOR, pos, DRAW_RADIUS)
            msg = {
                "type": "draw",
                "pos": pos,
                "color": DRAW_COLOR,
                "radius": DRAW_RADIUS,
            }
        send_msg(sock, msg)


def initialize_pygame():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Client")

    canvas = pygame.Surface((WIDTH, HEIGHT))
    canvas.fill(BG_COLOR)
    pygame.mouse.set_visible(False)
    pygame.display.flip()

    return screen, canvas


def main():
    screen, canvas = initialize_pygame()
    drawing, running, erase_mode = False, True, False
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    erase_mode = not erase_mode

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    drawing = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    drawing = False

            handle_mouse_motion(event, drawing, erase_mode, canvas, sock)

        screen.blit(canvas, (0, 0))
        if pygame.mouse.get_focused():
            current_pos = pygame.mouse.get_pos()
            draw_cursor(screen, current_pos, erase_mode)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

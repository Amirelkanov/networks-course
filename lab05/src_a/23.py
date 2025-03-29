import argparse
import os
import socket
import ssl
import base64
import sys

from const import CRLF, IMG_EXTENSIONS


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Simple Python SMTP Client using sockets for lab05A"
    )
    parser.add_argument(
        "--sender_email",
        type=str,
        default="st094559@student.spbu.ru",
        help="Sender email address",
    )
    parser.add_argument(
        "--sender_password",
        type=str,
        required=True,
        help="Sender password",
    )
    parser.add_argument(
        "--receiver_email",
        type=str,
        default="amirelkanov@yandex.ru",
        help="Receiver email address",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="TXT",
        choices=["TXT", "IMG"],
        help="Set the mail mode",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="Email from Python Socket Client",
        help="Email subject",
    )
    parser.add_argument(
        "--smtp_server",
        type=str,
        default="smtp.mail.ru",
        help="SMTP server address",
    )
    parser.add_argument(
        "--smtp_port",
        type=int,
        default=587,
        help="SMTP server port",
    )
    return parser.parse_args()


def process_input(mode):
    if mode == "TXT":
        return input("Enter text message: ")
    elif mode == "IMG":
        filename = input("Enter image filename: ")
        if not any(filename.lower().endswith(ext) for ext in IMG_EXTENSIONS):
            print(
                f"Error: Only {(', ').join(IMG_EXTENSIONS)} files are supported in IMG mode."
            )
            sys.exit(1)
        if os.path.exists(filename):
            print(f"File {filename} found. Sending its content...")
            with open(filename, "rb") as file:
                content = file.read()
            return content, filename
        else:
            print(f"Error: File '{filename}' not found.")
            sys.exit(1)


def recv_response(sock):
    response = sock.recv(1024).decode()
    print("Server:", response.strip())
    return response


def send_command(sock, command):
    print("Client:", command.strip())
    sock.sendall((command + CRLF).encode())
    return recv_response(sock)


def send_mail_socket(
    sender_email,
    sender_password,
    receiver_email,
    content,
    subject,
    smtp_server,
    smtp_port,
    is_image=False,
    filename=None,
):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((smtp_server, smtp_port))
        recv_response(sock)

        hostname = "localhost"
        send_command(sock, f"EHLO {hostname}")

        if smtp_port == 587:
            send_command(sock, "STARTTLS")
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=smtp_server)
            # Re-send EHLO after starting TLS
            send_command(sock, f"EHLO {hostname}")

        send_command(sock, "AUTH LOGIN")
        encoded_user = base64.b64encode(sender_email.encode()).decode()
        send_command(sock, encoded_user)
        encoded_pass = base64.b64encode(sender_password.encode()).decode()
        send_command(sock, encoded_pass)

        send_command(sock, f"MAIL FROM:<{sender_email}>")
        send_command(sock, f"RCPT TO:<{receiver_email}>")
        send_command(sock, "DATA")

        mime_type = "application/octet-stream"
        if is_image and filename:
            for ext in IMG_EXTENSIONS:
                if filename.lower().endswith(ext):
                    mime_type = "image/" + ext[1:]
                    break

            encoded_image = base64.b64encode(content).decode()

            message = (
                f"Subject: {subject}{CRLF}"
                f"From: {sender_email}{CRLF}"
                f"To: {receiver_email}{CRLF}"
                "MIME-Version: 1.0"
                + CRLF
                + f'Content-Type: {mime_type}; name="{filename}"{CRLF}'
                "Content-Transfer-Encoding: base64"
                + CRLF
                + f'Content-Disposition: attachment; filename="{filename}"{CRLF}'
                f"{CRLF}"
                f"{encoded_image}{CRLF}"
                f".{CRLF}"
            )
        else:
            message = (
                f"Subject: {subject}{CRLF}"
                f"From: {sender_email}{CRLF}"
                f"To: {receiver_email}{CRLF}"
                f"{CRLF}"
                f"{content}{CRLF}"
                f".{CRLF}"
            )

        print("Client: Sending email content...")
        sock.sendall(message.encode())
        recv_response(sock)

        send_command(sock, "QUIT")
        sock.close()
        print("Email sent successfully!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    args = parse_arguments()
    print(f"Running with arguments: {args}")

    if args.mode == "TXT":
        content = process_input(args.mode)
        is_image = False
        filename = None
    else:
        content, filename = process_input(args.mode)
        is_image = True

    send_mail_socket(
        args.sender_email,
        args.sender_password,
        args.receiver_email,
        content,
        args.subject,
        args.smtp_server,
        args.smtp_port,
        is_image,
        filename,
    )

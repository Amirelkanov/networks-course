import argparse
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def parse_arguments():
    parser = argparse.ArgumentParser(description="simple python mail client for lab05A")
    parser.add_argument(
        "--sender_email",
        type=str,
        default="st094559@student.spbu.ru",
        help="sender email address",
    )
    parser.add_argument(
        "--sender_password",
        type=str,
        required=True,
        help="sender password",
    )
    parser.add_argument(
        "--receiver_email",
        type=str,
        default="amirelkanov@yandex.ru",
        help="receiver email address",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="TEXT",
        choices=["TEXT", "FILE"],
        help="set the mail mode. For FILE mode .txt and .html only supported.",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="Email from Python Script",
        help="email subject",
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
    if mode == "TEXT":
        return input("Enter text message: ")
    elif mode == "FILE":
        filename = input("Enter filename: ")
        if os.path.exists(filename):
            print(f"File {filename} has been found. Sending its content...")
            with open(filename, "r", encoding="utf-8") as file:
                content = file.read()
                return content, filename
        else:
            print(f"Error: File '{filename}' not found.")
            exit(1)


def send_mail(
    sender_email,
    sender_password,
    receiver_email,
    content,
    subject,
    smtp_server,
    smtp_port,
    is_html,
):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    content_type = "html" if is_html else "plain"
    message.attach(MIMEText(content, content_type))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)

            print("Email sent successfully!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    args = parse_arguments()

    print(f"Running with arguments: {args}")

    if args.mode == "TEXT":
        content = process_input(args.mode)
        is_html = False
    else:
        content, filename = process_input(args.mode)
        is_html = filename.lower().endswith(".html")

    # Навалил дрилла с миллионом аргументов...
    send_mail(
        args.sender_email,
        args.sender_password,
        args.receiver_email,
        content,
        args.subject,
        args.smtp_server,
        args.smtp_port,
        is_html,
    )

import socket
from const import BUF_SIZE, FTP_PORT
from exception import (
    FTPConnectionError,
    FTPCommandError,
    FTPClientException,
    FTPLoginError,
)


class FTPClient:
    def __init__(self, host, port=FTP_PORT, user="anonymous", passwd="anonymous@"):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.sock = None  # Control connection socket
        self.buffer_size = BUF_SIZE

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print(self._get_response())  # Welcome msg
        except socket.error as e:
            raise FTPConnectionError(f"Failed to connect: {e}")

    def login(self):
        try:
            response = self.send_command("USER " + self.user)
            response = self.send_command("PASS " + self.passwd)
            if response.startswith("5"):
                raise FTPLoginError(response)
        except FTPClientException as e:
            raise FTPClientException(f"Login failed: {e}")

    def send_command(self, cmd):
        try:
            if not cmd.endswith("\r\n"):
                cmd += "\r\n"
            # Privacy!!!
            print(
                f"Client: {'PASS ***' if cmd.strip().startswith("PASS") else cmd.strip()}"
            )
            self.sock.sendall(cmd.encode("utf-8"))
            response = self._get_response()
            print("Server:", response.strip())
            return response
        except socket.error as e:
            raise FTPCommandError(f"Failed to send command: {e}")

    def enter_passive_mode(self):
        try:
            response = self.send_command("PASV")
            print("PASV response:", response)

            # Parsing response format: 227 Entering Passive Mode (h1,h2,h3,h4,p1,p2).
            start = response.find("(")
            end = response.find(")", start + 1)
            if start == -1 or end == -1:
                raise FTPCommandError("Failed to parse PASV response")
            pasv_data = response[start + 1 : end]
            parts = pasv_data.split(",")
            ip = ".".join(parts[:4])
            port = (int(parts[4]) << 8) + int(parts[5])

            return ip, port
        except Exception as e:
            raise FTPCommandError(f"Failed to enter passive mode: {e}")

    def list_files(self):
        try:
            ip, port = self.enter_passive_mode()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))

            self.send_command("LIST")
            data = b""
            while True:
                chunk = data_sock.recv(self.buffer_size)
                if not chunk:
                    break
                data += chunk
            data_sock.close()

            print("Directory listing:\n" + data.decode("utf-8"))
            print(self._get_response())
        except Exception as e:
            raise FTPClientException(f"Failed to list files: {e}")

    def download_file(self, remote_filename, local_filename):
        try:
            ip, port = self.enter_passive_mode()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))

            self.send_command("RETR " + remote_filename)
            with open(local_filename, "wb") as f:
                while True:
                    chunk = data_sock.recv(self.buffer_size)
                    if not chunk:
                        break
                    f.write(chunk)
            data_sock.close()

            print("Download complete. Local file saved as:", local_filename)
            print(self._get_response())
        except Exception as e:
            raise FTPClientException(f"Failed to download file: {e}")

    def upload_file(self, local_filename, remote_filename):
        try:
            ip, port = self.enter_passive_mode()
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_sock.connect((ip, port))

            self.send_command("STOR " + remote_filename)
            with open(local_filename, "rb") as f:
                while True:
                    chunk = f.read(self.buffer_size)
                    if not chunk:
                        break
                    data_sock.sendall(chunk)
            data_sock.close()
            print("Upload complete. Remote file saved as:", remote_filename)
            print(self._get_response())
        except Exception as e:
            raise FTPClientException(f"Failed to upload file: {e}")

    def quit(self):
        try:
            self.send_command("QUIT")
            self.sock.close()
        except Exception as e:
            raise FTPClientException(f"Failed to quit: {e}")

    def _get_response(self):
        try:
            response = ""
            while True:
                data = self.sock.recv(self.buffer_size).decode("utf-8")
                response += data
                # FTP response lines end with CRLF
                if "\r\n" in response:
                    break
            return response
        except socket.error as e:
            raise FTPCommandError(f"Failed to receive response: {e}")

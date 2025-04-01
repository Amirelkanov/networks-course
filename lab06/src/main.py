from ftp import FTPClient


def cmd_mode():
    while True:
        try:
            host = input("Enter FTP server address: ").strip()
            user = input("Enter username (default: anonymous): ").strip()
            passwd = input("Enter password (default: anonymous@): ").strip()

            ftp = FTPClient(host, user=user, passwd=passwd)
            ftp.connect()
            ftp.login()
            break
        except KeyboardInterrupt as e:
            print("\nExiting...")
            exit(0)
        except Exception as e:
            print(f"Connection failed: {e}")

    while True:
        try:
            print("\nAvailable commands: list, download, upload, quit (or CTRL+C)")
            command = input("Enter command: ").strip().lower()
            if command == "list":
                ftp.list_files()
            elif command == "download":
                remote_file = input("Enter remote filename to download: ")
                local_file = input("Enter local filename to save as: ")
                ftp.download_file(remote_file, local_file)
            elif command == "upload":
                local_file = input("Enter local filename to upload: ")
                remote_file = input("Enter remote filename to save as: ")
                ftp.upload_file(local_file, remote_file)
            elif command == "quit":
                ftp.quit()
                break
            else:
                print("Unknown command. Please try again.")
        except KeyboardInterrupt as e:
            print("\nExiting...")
            ftp.quit()
            exit(0)
        except Exception as e:
            print(f"Command failed: {e}\n")


if __name__ == "__main__":
    cmd_mode()

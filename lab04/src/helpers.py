# Parse HTTP request data into headers and body.
from urllib.parse import urlparse

from const import BUF_SIZE


def parse_http_request(request_data):
    header_data, _, body = request_data.partition(b"\r\n\r\n")
    header_lines = header_data.decode("utf-8", errors="replace").split("\r\n")

    if len(header_lines) < 1:
        return None, None, None, None, None, 0

    request_line = header_lines[0]
    parts = request_line.split()
    if len(parts) != 3:
        return header_lines, None, None, None, body, 0

    method, path, version = parts

    content_length = next(
        (
            int(h.split(":", 1)[1].strip())
            for h in header_lines[1:]
            if h.lower().startswith("content-length:")
        ),
        0,
    )

    return header_lines, method, path, version, body, content_length


# Extract target hostname, port and path from the request path.
def extract_target_info(path):
    target = path.lstrip("/")
    if not (target.startswith("http://") or target.startswith("https://")):
        target = "http://" + target

    parsed_url = urlparse(target)
    hostname = parsed_url.hostname
    if not hostname:
        return None, None, None, target

    port = parsed_url.port if parsed_url.port else 80
    remote_path = parsed_url.path if parsed_url.path else "/"
    if parsed_url.query:
        remote_path += "?" + parsed_url.query

    return hostname, port, remote_path, target


def build_remote_request(method, remote_path, version, header_lines, hostname, body):
    new_request_line = f"{method} {remote_path} {version}\r\n"
    new_headers = []
    host_header_present = False

    for header in header_lines[1:]:
        if ":" not in header:
            continue

        header_name, header_value = header.split(":", 1)
        header_name, header_value = header_name.strip().lower(), header_value.strip()

        if header_name in ["proxy-connection", "connection"]:
            continue

        if header_name == "host":
            host_header_present = True
            new_headers.append(f"Host: {hostname}")
        else:
            new_headers.append(f"{header_name.capitalize()}: {header_value}")

    if not host_header_present:
        new_headers.append(f"Host: {hostname}")

    new_headers.append("Connection: close")

    request_message = new_request_line + "\r\n".join(new_headers) + "\r\n\r\n"
    return request_message.encode() + body


def relay_response(remote_socket, connection_socket):
    response_data = b""
    response_code = "N/A"
    headers_received = False

    while True:
        remote_data = remote_socket.recv(BUF_SIZE)
        if not remote_data:
            break

        response_data += remote_data
        connection_socket.sendall(remote_data)

        # Extract response code from the first line if not done yet
        if not headers_received and b"\r\n" in response_data:
            headers_received = True
            response_line = response_data.split(b"\r\n")[0].decode(errors="ignore")
            status_parts = response_line.split()
            response_code = status_parts[1] if len(status_parts) >= 2 else "N/A"

    return response_code

import os
import socket


def notify(*fields: str) -> None:
    """Send a message to the systemd notification socket, if one is configured."""
    notify_socket = os.environ.get("NOTIFY_SOCKET")
    if not notify_socket:
        return

    if notify_socket.startswith("@"):
        notify_socket = "\0" + notify_socket[1:]

    message = "\n".join(fields).encode()

    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.connect(notify_socket)
        sock.sendall(message)


def notify_status(status: str) -> None:
    notify(f"STATUS={status}")

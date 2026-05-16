"""Entry point for ``python -m mood.client``."""
import socket
import sys
import threading

from mood.client.shell import MUD_SH, reader_thread
from mood.common.constants import HOST, PORT


def main():
    """Connect to the server and run the command loop."""
    if len(sys.argv) < 2:
        print("Usage: python -m mood.client <username>")
        sys.exit(1)

    username = sys.argv[1]
    if not username or " " in username:
        print("Username must be a non-empty string without spaces")
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        sock.sendall(f"{username}\n".encode("utf-8"))

        buffer = b""
        while b"\n" not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                print("Connection closed by server")
                sys.exit(1)
            buffer += chunk
        line, buffer = buffer.split(b"\n", 1)
        greeting = line.decode("utf-8", errors="replace")
        print(greeting)
        if not greeting.startswith("Connected as "):
            sys.exit(1)

        mud = MUD_SH(sock)
        reader = threading.Thread(
            target=reader_thread,
            args=(sock, mud, buffer),
            daemon=False,
        )
        reader.start()
        try:
            mud.cmdloop()
        finally:
            mud.closing = True
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            reader.join(timeout=1.0)


if __name__ == "__main__":
    main()

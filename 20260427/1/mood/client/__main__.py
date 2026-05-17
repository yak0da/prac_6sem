"""Entry point for ``python -m mood.client``."""
import socket
import sys
import threading

from mood.client.shell import MUD_SH, reader_thread, run_cmdfile
from mood.common.constants import HOST, PORT


def parse_args(argv):
    """Parse username and optional ``--file`` argument."""
    username = None
    cmdfile = None
    i = 1
    while i < len(argv):
        if argv[i] == "--file":
            i += 1
            if i >= len(argv):
                return None, None
            cmdfile = argv[i]
            i += 1
        elif username is None:
            username = argv[i]
            i += 1
        else:
            return None, None
    return username, cmdfile


def main():
    """Connect to the server and run the command loop."""
    username, cmdfile = parse_args(sys.argv)
    if not username:
        print("Usage: python -m mood.client <username> [--file <filename>]")
        sys.exit(1)
    if not username or " " in username:
        print("Username must be a non-empty string without spaces")
        sys.exit(1)
    if cmdfile is not None:
        try:
            open(cmdfile, encoding="utf-8").close()
        except OSError as exc:
            print(exc)
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
        if cmdfile is not None:
            mud.script_mode = True
        reader = threading.Thread(
            target=reader_thread,
            args=(sock, mud, buffer),
            daemon=False,
        )
        reader.start()
        try:
            if cmdfile is not None:
                run_cmdfile(mud, cmdfile)
            else:
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

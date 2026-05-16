import socket
import sys
import shlex
import threading
import readline

from cowsay import list_cows

import cmd

WEAPONS = {"sword": 10, "spear": 15, "axe": 20}


class MUD_SH(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "> "

    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.lock = threading.Lock()

    def display(self, message):
        with self.lock:
            line = readline.get_line_buffer()
            sys.stdout.write("\r\033[K")
            print(message, end="" if message.endswith("\n") else "\n")
            sys.stdout.write(self.prompt + line)
            sys.stdout.flush()

    def send_command(self, data):
        if not data.endswith("\n"):
            data += "\n"
        self.sock.sendall(data.encode("utf-8"))

    def do_up(self, arg):
        self.send_command("move 0 -1")

    def do_down(self, arg):
        self.send_command("move 0 1")

    def do_left(self, arg):
        self.send_command("move -1 0")

    def do_right(self, arg):
        self.send_command("move 1 0")

    def do_addmon(self, arg):
        """addmon <monster_name> hello <hello_string> hp <hitpoints> coords <x> <y>"""
        try:
            parts = shlex.split(arg)
            monster_name = parts[0]
            if monster_name not in [*list_cows(), "jgsbat"]:
                print("Cannot add unknown monster")
                return
            hello_string = parts[1 + parts.index("hello")]
            hitpoints = int(parts[1 + parts.index("hp")])
            i = parts.index("coords")
            x, y = int(parts[i + 1]), int(parts[i + 2])
            data = (
                f"addmon {shlex.quote(hello_string)} {hitpoints} "
                f"{shlex.quote(monster_name)} {x} {y}"
            )
            self.send_command(data)
        except Exception:
            print("Invalid arguments")

    def do_EOF(self, arg):
        print()
        return True

    def do_sayall(self, arg):
        """sayall <строка>"""
        try:
            parts = shlex.split(arg)
            if len(parts) != 1:
                print("Invalid arguments")
                return
            self.send_command(f"sayall {shlex.quote(parts[0])}")
        except Exception:
            print("Invalid arguments")

    def do_attack(self, arg):
        """attack <monster_name> with <weapon_name>"""
        parts = shlex.split(arg)
        try:
            if len(parts) == 3 and parts[1] == "with":
                if parts[2] not in WEAPONS:
                    print("Unknown weapon")
                    return
                monster, weapon = parts[0], parts[2]
            elif len(parts) == 1:
                monster, weapon = parts[0], "sword"
            else:
                print("Invalid arguments")
                return
            self.send_command(f"attack {monster} {weapon}")
        except Exception:
            print("Invalid arguments")

    def complete_attack(self, text, line, begidx, endidx):
        parts = shlex.split(line)
        if "with" in parts:
            with_idx = parts.index("with")
            if len(parts) == with_idx + 2:
                return [w for w in WEAPONS if w.startswith(text)]
        elif len(parts) == 2:
            monsters = [*list_cows(), "jgsbat"]
            return [m for m in monsters if m.startswith(text)]
        return []


def reader_thread(sock, mud, initial=b""):
    buffer = initial
    while True:
        if b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            mud.display(line.decode("utf-8", errors="replace"))
            continue
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk


def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    if not username or " " in username:
        print("Username must be a non-empty string without spaces")
        sys.exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", 1111))
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
        threading.Thread(
            target=reader_thread, args=(sock, mud, buffer), daemon=True
        ).start()
        mud.cmdloop()


if __name__ == "__main__":
    main()
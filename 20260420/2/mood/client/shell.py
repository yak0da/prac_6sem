"""Interactive MOOD client command shell."""

import shlex
import socket
import sys
import threading
import time

import cmd
import readline
from cowsay import list_cows

from mood.common.constants import WEAPONS
from mood.common.monsters import KNOWN_MONSTERS

CMD_INTERVAL_SEC = 1


class MUD_SH(cmd.Cmd):
    """Cmd-based shell for sending MOOD commands."""

    intro = "<<< Welcome to MOOD 0.1 >>>"
    prompt = "> "

    def __init__(self, sock):
        """Attach to the server socket."""
        super().__init__()
        self.sock = sock
        self.lock = threading.Lock()
        self.last_cmd = ""
        self.closing = False
        self.script_mode = False

    def emptyline(self):
        """Do nothing on an empty line."""

    def precmd(self, line):
        """Remember the last entered command."""
        self.last_cmd = line.strip()
        return line

    def display(self, message):
        """Print a server message without losing input."""
        if self.closing:
            return
        if self.script_mode:
            end = "" if message.endswith("\n") else "\n"
            print(message, end=end)
            return
        with self.lock:
            line = readline.get_line_buffer()
            if line.strip() == self.last_cmd:
                line = ""
            sys.stdout.write("\r\033[K")
            end = "" if message.endswith("\n") else "\n"
            print(message, end=end)
            sys.stdout.write(self.prompt + line)
            sys.stdout.flush()
            readline.redisplay()

    def send_command(self, data):
        """Send a command line to the server."""
        if not data.endswith("\n"):
            data += "\n"
        self.sock.sendall(data.encode("utf-8"))
        if self.script_mode:
            time.sleep(CMD_INTERVAL_SEC)

    def do_up(self, _arg):
        """Send move up."""
        self.send_command("move 0 -1")

    def do_down(self, _arg):
        """Send move down."""
        self.send_command("move 0 1")

    def do_left(self, _arg):
        """Send move left."""
        self.send_command("move -1 0")

    def do_right(self, _arg):
        """Send move right."""
        self.send_command("move 1 0")

    def do_addmon(self, arg):
        """Add a monster: addmon NAME hello TEXT hp N coords X Y."""
        try:
            parts = shlex.split(arg)
            monster_name = parts[0]
            if monster_name not in KNOWN_MONSTERS:
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
        except (ValueError, IndexError):
            print("Invalid arguments")

    def do_EOF(self, _arg):
        """Exit the client."""
        self.closing = True
        print()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        return True

    def do_sayall(self, arg):
        """Broadcast a message: sayall WORD or sayall \"text\"."""
        try:
            parts = shlex.split(arg)
            if len(parts) != 1:
                print("Invalid arguments")
                return
            self.send_command(f"sayall {shlex.quote(parts[0])}")
        except ValueError:
            print("Invalid arguments")

    def do_attack(self, arg):
        """Attack a monster: attack NAME [with WEAPON]."""
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
        except ValueError:
            print("Invalid arguments")

    def do_movemonsters(self, arg):
        """Turn wandering monsters on or off."""
        if arg not in ("on", "off"):
            print("Invalid arguments")
            return
        self.send_command(f"movemonsters {arg}")

    def do_locale(self, arg):
        """Set message locale: locale ru_RU.UTF-8."""
        if not arg.strip():
            print("Invalid arguments")
            return
        self.send_command(f"locale {arg.strip()}")

    def complete_attack(self, text, line, begidx, endidx):
        """Complete monster or weapon names for attack."""
        del begidx, endidx
        parts = shlex.split(line)
        if "with" in parts:
            with_idx = parts.index("with")
            if len(parts) == with_idx + 2:
                return [w for w in WEAPONS if w.startswith(text)]
        elif len(parts) == 2:
            monsters = [*list_cows(), "jgsbat"]
            return [m for m in monsters if m.startswith(text)]
        return []


def run_cmdfile(mud, filename):
    """Run shell commands from a file instead of interactive input."""
    mud.script_mode = True
    mud.use_rawinput = False
    mud.prompt = ""
    with open(filename, encoding="utf-8") as cmdfile:
        mud.stdin = cmdfile
        mud.cmdloop()


def reader_thread(sock, mud, initial=b""):
    """Read server messages in a background thread."""
    buffer = initial
    try:
        while not mud.closing:
            if b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                mud.display(line.decode("utf-8", errors="replace"))
                continue
            try:
                chunk = sock.recv(4096)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk
    except OSError:
        pass

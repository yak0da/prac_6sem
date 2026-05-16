import socket
import shlex
from io import StringIO
from cowsay import cowsay, list_cows, read_dot_cow
import cmd

jgsbat = read_dot_cow(StringIO(r"""
$the_cow = <<EOC;
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
EOC
"""))

def move(self, x, y):
    data = f"move {x} {y}\n"
    self.socket.sendall(data.encode())
    output = self.socket.recv(1024).decode().split("\n")
    print(output[0])
    if len(output) > 1:
        name = output[1]
        hello = output[2]
        if name == "jgsbat":
            print(cowsay(hello, cowfile=jgsbat))
        else:
            print(cowsay(hello, cow=name))



class MUD_SH(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "> "

    def __init__(self, Socket):
        super().__init__()
        self.socket = Socket

    def do_up(self, arg):
        move(self, 0, -1)

    def do_down(self, arg):
        move(self, 0, 1)

    def do_left(self, arg):
        move(self, -1, 0)

    def do_right(self, arg):
        move(self, 1, 0)
    
    def do_addmon(self, arg):
        """addmon <monster_name> hello <hello_string> hp <hitpoints> coords <x> <y>"""
        try:
            parts = shlex.split(arg)
            monster_name = parts[0]
            if not monster_name in [*list_cows(), "jgsbat"]:
                print("Cannot add unknown monster")
                return
            hello_string = parts[1 + parts.index("hello")]
            hitpoints = int(parts[1 + parts.index("hp")])
            i = parts.index("coords")
            x, y = int(parts[i + 1]), int(parts[i + 2])
            data = f"addmon {shlex.quote(hello_string)} {hitpoints} {shlex.quote(monster_name)} {x} {y}\n"
            self.socket.sendall(data.encode("utf-8"))
            print(self.socket.recv(1024).decode("utf-8", errors="replace"))
        except Exception:
            print("Invalid arguments")

    def do_EOF(self, arg):
        print()
        return True
    
    def do_attack(self, arg):
        """attack <monster_name> with <weapon_name>"""
        parts = shlex.split(arg)
        weapons = {"sword": 10, "spear": 15, "axe": 20}
        try:
            if len(parts) == 3 and parts[1] == "with":
                if not parts[2] in weapons.keys():
                    print("Unknown weapon")
                    return
                data = f"attack {parts[0]} {weapons[parts[2]]}\n"
            elif len(parts) == 1:
                data = f"attack {parts[0]} {weapons['sword']}\n"
            self.socket.sendall(data.encode("utf-8"))
            print(self.socket.recv(1024).decode("utf-8", errors="replace"))
        except Exception:
            print("Invalid arguments")

    def complete_attack(self, text, line, begidx, endidx):
        parts = shlex.split(line)
        if "with" in parts:
            with_idx = parts.index("with")
            if len(parts) == with_idx + 2:
                weapons = ["sword", "spear", "axe"]
                return [w for w in weapons if w.startswith(text)]
        else:
            if len(parts) == 2:
                monsters = [*list_cows(), "jgsbat"]
                return [m for m in monsters if m.startswith(text)]
        return []


def main():
    host = "127.0.0.1"
    port = 1111
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        print("клиент подключился к серверу")

        MUD_SH(client_socket).cmdloop()


if __name__ == "__main__":
    main()
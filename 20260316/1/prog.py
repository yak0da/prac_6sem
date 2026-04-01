import sys
import shlex
from io import StringIO
from cowsay import cowsay, list_cows, read_dot_cow
import cmd
import readline

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

class Monster:
    def __init__(self, name, hello_string, hitpoints):
        self.name = name
        self.hello = hello_string
        self.hitpoints = hitpoints
    def encounter(self):
        if self.name == "jgsbat":
            return cowsay(self.hello, cowfile=jgsbat)
        return cowsay(self.hello, cow=self.name)

class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
    def move(self, dx, dy):
        self.x = (self.x + dx) % 10
        self.y = (self.y + dy) % 10
        return self.x, self.y
    
class Game:
    def __init__(self):
        self.field = [[None] * 10 for _ in range(10)]
        self.player = Player()

    def move(self, dx, dy):
        x, y = self.player.move(dx, dy)
        output = [f"Moved to ({x}, {y})"]
        if self.field[x][y]:
            output.append(self.field[x][y].encounter())
        return "\n".join(output)
    
    def add_monster(self, hello, hp, name, x, y):
        if not name in [*list_cows(), "jgsbat"]:
            return "Cannot add unknown monster"
        output = [f"Added monster {name} to ({x}, {y}) saying {hello}"]
        if self.field[x][y]:
            output.append("Replaced the old monster")
        self.field[x][y] = Monster(name, hello, hp)
        return "\n".join(output)
    def attack(self, monster_name, weapon_name="sword"):
        if not weapon_name in self.player.weapons.keys():
            return "Unknown weapon"
        damage = self.player.weapons[weapon_name]
        x = self.player.x
        y = self.player.y
        monster = self.field[x][y]
        if (not monster) or monster.name != monster_name:
            return f"No {monster_name} here"
        if monster.hitpoints >= damage:
            monster.hitpoints -= damage
        else:
            damage = monster.hitpoints
            monster.hitpoints = 0

        output = [f"Attacked {monster.name}, damage {damage} hp"]

        if monster.hitpoints == 0:
            self.field[x][y] = None
            output.append(f"{monster.name} died")
        else:
            output.append(f"{monster.name} now has {monster.hitpoints}")
        return "\n".join(output)
        
    
class MUD_SH(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "> "

    def __init__(self):
        super().__init__()
        self.game = Game()

    def do_up(self, arg):
        print(self.game.move(0, -1))
    def do_down(self, arg):
        print(self.game.move(0, 1))
    def do_left(self, arg):
        print(self.game.move(-1, 0))
    def do_right(self, arg):
        print(self.game.move(1, 0))
    
    def do_addmon(self, arg):
        """addmon <monster_name> hello <hello_string> hp <hitpoints> coords <x> <y>"""
        try:
            parts = shlex.split(arg)
            monster_name = parts[0]
            hello_string = parts[1 + parts.index("hello")]
            hitpoints = int(parts[1 + parts.index("hp")])
            i = parts.index("coords")
            x, y = int(parts[i + 1]), int(parts[i + 2])

            print(self.game.add_monster(hello_string, hitpoints, monster_name, x, y))
        except Exception:
            print("Invalid arguments")

    def do_EOF(self, arg):
        print()
        return True
    
    def do_attack(self, arg):
        """attack <monster_name> with <weapon_name>"""
        parts = shlex.split(arg)
        try:
            if len(parts) == 3 and parts[1] == "with":
                print(self.game.attack(parts[0], parts[2]))
            else:
                print(self.game.attack(parts[0]))
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

if __name__ == "__main__":
    MUD_SH().cmdloop()
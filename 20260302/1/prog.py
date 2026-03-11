import sys
import shlex
from io import StringIO
from cowsay import cowsay, list_cows, read_dot_cow

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
    def __init__(self, name, hello, hitpoints, coords):
        self.name = name
        self.hello = hello
        self.hitpoints = hitpoints
        self.x, self.y = coords

def encounter(obj):
    name, hello = obj.name, obj.hello
    if name == "jgsbat":
        print(cowsay(hello, cowfile=jgsbat))
    else:
        print(cowsay(hello, cow=name))

def main():
    field = [[None for _ in range(10)] for _ in range(10)]
    curX, curY = 0, 0

    # старт
    print("<<< Welcome to Python-MUD 0.1 >>>")

    for line in sys.stdin:

        line = line.strip()
        if line in ["up", "down", "left", "right"]:
            match line:
                case "up":
                    curY = (curY-1) % 10
                case "down":
                    curY = (curY+1) % 10
                case "left":
                    curX = (curX-1) % 10
                case "right":
                    curX = (curX+1) % 10
            print(f"Moved to ({curX}, {curY})")
            if field[curY][curX]:
                encounter(field[curY][curX])
            continue

        command = shlex.split(line)

        if not command or command[0] != "addmon":
            print("Invalid command")
            continue
        else:
            if len(command) != 9:
                print("Invalid arguments")
                continue
            if not command[1] in [*list_cows(), "jgsbat"]:
                print("Cannot add unknown monster")
                continue
            
            monster_name = command[1]
            try:
                i = command.index("hello")
                hello_string = command[i + 1]
                i = command.index("hp")
                hitpoints = int(command[i + 1])
                if hitpoints < 0:
                    raise ValueError("hp должно быть неотрицательным")
                i = command.index("coords")
                x, y = int(command[i + 1]), int(command[i + 2])
                if not (0 <= x < 9 and 0 <= y < 10):
                    raise ValueError("неверный диапазон для координат")
            except Exception:
                print("Invalid arguments")
                continue

            print(f"Added monster {monster_name} to ({x}, {y}) saying {hello_string}")
            if field[y][x]:
                print("Replaced the old monster")
            field[y][x] = Monster(monster_name, hello_string, hitpoints, (x, y))


if __name__ == "__main__":
    main()
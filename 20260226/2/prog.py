import sys
from cowsay import cowsay

field = [["" for _ in range(10)] for _ in range(10)]
curX, curY = 0, 0

def encounter(x: int, y: int, text: str):
    print(cowsay(text))

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
            encounter(curX, curY, field[curY][curX])
        continue

    command = line.split()
    if command[0] == "addmon":
        if len(command) == 5 and command[2].isdigit() and command[3].isdigit(): # а
            name = command[1]         # а
            hello = command[4]        # а
            x, y = int(command[2]), int(command[3]) # а
            print(f"Added monster {name} to ({x}, {y}) saying {hello}")     # а
            if field[y][x]:
                print("Replaced the old monster")
            field[y][x] = (name, hello)         # а
        else:
            print("Invalid arguments")
    else:
        print("Invalid command")

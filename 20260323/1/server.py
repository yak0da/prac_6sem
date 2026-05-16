import socket
import shlex
from io import StringIO

class Monster:
    def __init__(self, name, hello_string, hitpoints):
        self.name = name
        self.hello = hello_string
        self.hitpoints = hitpoints

class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
    def move(self, dx, dy):
        self.x = (self.x + dx) % 10
        self.y = (self.y + dy) % 10
        return self.x, self.y
    
class Game:
    def __init__(self):
        self.field = [[None] * 10 for _ in range(10)]
        self.player = Player()

    def move(self, dx: int, dy: int) -> str:
        x, y = self.player.move(dx, dy)
        output = [f"Moved to ({x}, {y})"]
        if self.field[x][y]:
            output.append(f"{self.field[x][y].name}")
            output.append(f"{self.field[x][y].hello}")
        return "\n".join(output)
    
    def add_monster(self, hello: str, hp: int, name: str, x: int, y: int) -> str:
        output = [f"Added monster {name} to ({x}, {y}) saying {hello}"]
        if self.field[x][y]:
            output.append("Replaced the old monster")
        self.field[x][y] = Monster(name, hello, hp)
        return "\n".join(output)

    def attack(self, monster_name: str, damage: int) -> str:
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

game = Game()

def proccessed_data(data: str) -> str:
    parts = shlex.split(data)
    # будем считать все параметры позиционными
    match parts[0]:
        case "move":
            # move [dx] [dy]
            return game.move(int(parts[1]), int(parts[2]))
        case "addmon":
            # addmon [hello] [hp] [name] [x] [y]
            return game.add_monster(parts[1], int(parts[2]), parts[3], int(parts[4]), int(parts[5]))
        # attack [name] [damage]
        case "attack":    
            return game.attack(parts[1], int(parts[2]))



def main():
    host = "127.0.0.1"
    port = 1111
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:

        socket_server.bind((host, port))
        socket_server.listen(1)
        
        conn, addr = socket_server.accept()

        with conn:
            while True:
                data = conn.recv(1024).decode("utf-8", errors="replace").strip()
                if not data:
                    break
                response = proccessed_data(data)
                conn.sendall(response.encode("utf-8"))

            
if __name__ == "__main__":
    main()
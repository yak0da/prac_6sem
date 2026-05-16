import asyncio
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

KNOWN_MONSTERS = frozenset([*list_cows(), "jgsbat"])


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
        self.players = {}

    def add_player(self, username):
        self.players[username] = Player()

    def remove_player(self, username):
        self.players.pop(username, None)

    def move(self, username, dx, dy):
        player = self.players[username]
        x, y = player.move(dx, dy)
        unicast = [f"Moved to ({x}, {y})"]
        monster = self.field[x][y]
        if monster:
            unicast.append(monster.encounter())
        return unicast, []

    def add_monster(self, username, hello, hp, name, x, y):
        if name not in KNOWN_MONSTERS:
            return ["Cannot add unknown monster"], []
        self.field[x][y] = Monster(name, hello, hp)
        broadcast = [f"{username} placed monster {name} with {hp} hp at ({x}, {y})"]
        return [], broadcast

    def attack(self, username, monster_name, weapon_name):
        player = self.players[username]
        if weapon_name not in player.weapons:
            return ["Unknown weapon"], []
        damage = player.weapons[weapon_name]
        x, y = player.x, player.y
        monster = self.field[x][y]
        if not monster or monster.name != monster_name:
            return [f"No {monster_name} here"], []

        if monster.hitpoints >= damage:
            monster.hitpoints -= damage
        else:
            damage = monster.hitpoints
            monster.hitpoints = 0

        msg = (
            f"{username} attacked {monster.name} with {weapon_name}, "
            f"damage {damage} hp, {monster.name} has {monster.hitpoints} hp left"
        )
        if monster.hitpoints == 0:
            self.field[x][y] = None
            msg += f", {monster.name} was killed"
        return [], [msg]


game = Game()
clients = {}


def valid_username(username):
    return bool(username) and " " not in username and "\n" not in username


async def send_line(writer, message):
    if not message.endswith("\n"):
        message += "\n"
    writer.write(message.encode("utf-8"))
    await writer.drain()


def schedule_send(writer, message):
    asyncio.create_task(send_line(writer, message))


def schedule_broadcast(message):
    for writer in clients.values():
        schedule_send(writer, message)


def schedule_unicast(username, message):
    writer = clients.get(username)
    if writer:
        schedule_send(writer, message)


def process_command(username, data):
    try:
        parts = shlex.split(data)
    except ValueError:
        return ["Invalid command"], []

    if not parts:
        return ["Invalid command"], []

    match parts[0]:
        case "move":
            if len(parts) != 3:
                return ["Invalid arguments"], []
            return game.move(username, int(parts[1]), int(parts[2]))
        case "addmon":
            if len(parts) != 6:
                return ["Invalid arguments"], []
            return game.add_monster(
                username, parts[1], int(parts[2]), parts[3], int(parts[4]), int(parts[5])
            )
        case "attack":
            if len(parts) != 3:
                return ["Invalid arguments"], []
            return game.attack(username, parts[1], parts[2])
        case _:
            return ["Invalid command"], []


async def handle_client(reader, writer):
    username = (await reader.readline()).decode("utf-8", errors="replace").strip()

    if not valid_username(username):
        await send_line(writer, "Invalid username")
        writer.close()
        await writer.wait_closed()
        return

    if username in clients:
        await send_line(writer, f"Username {username} is already connected")
        writer.close()
        await writer.wait_closed()
        return

    clients[username] = writer
    game.add_player(username)

    await send_line(writer, f"Connected as {username}")
    schedule_broadcast(f"{username} joined MUD")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            line = data.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            unicast, broadcast = process_command(username, line)
            for message in unicast:
                schedule_unicast(username, message)
            for message in broadcast:
                schedule_broadcast(message)
    finally:
        clients.pop(username, None)
        game.remove_player(username)
        schedule_broadcast(f"{username} left MUD")
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 1111)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())


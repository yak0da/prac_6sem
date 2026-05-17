"""Game world state and rules."""

import random

from cowsay import cowsay

from mood.common.constants import FIELD_SIZE, WEAPONS
from mood.common.monsters import KNOWN_MONSTERS, get_jgsbat

WANDER_DIRECTIONS = {
    (1, 0): "right",
    (-1, 0): "left",
    (0, -1): "up",
    (0, 1): "down",
}

WANDER_INTERVAL_SEC = 30


class Monster:
    """Monster on the field."""

    def __init__(self, name, hello_string, hitpoints):
        """Store monster attributes."""
        self.name = name
        self.hello = hello_string
        self.hitpoints = hitpoints

    def encounter(self):
        """Return cowsay greeting for this monster."""
        if self.name == "jgsbat":
            return cowsay(self.hello, cowfile=get_jgsbat())
        return cowsay(self.hello, cow=self.name)


class Player:
    """Player position and weapons."""

    def __init__(self):
        """Create player at origin."""
        self.x = 0
        self.y = 0
        self.weapons = dict(WEAPONS)

    def move(self, dx, dy):
        """Move on the field and return new coordinates."""
        self.x = (self.x + dx) % FIELD_SIZE
        self.y = (self.y + dy) % FIELD_SIZE
        return self.x, self.y


class Game:
    """Shared multiplayer game state."""

    def __init__(self):
        """Initialize empty field and players."""
        self.field = [[None] * FIELD_SIZE for _ in range(FIELD_SIZE)]
        self.players = {}
        self.moving_monsters = True

    def add_player(self, username):
        """Register a connected player."""
        self.players[username] = Player()

    def remove_player(self, username):
        """Remove a disconnected player."""
        self.players.pop(username, None)

    def set_moving_monsters(self, enabled):
        """Enable or disable wandering monsters."""
        self.moving_monsters = enabled
        state = "on" if enabled else "off"
        return [f"Moving monsters: {state}"], []

    def list_monster_cells(self):
        """Return ``(x, y, monster)`` for every occupied cell."""
        cells = []
        for x in range(FIELD_SIZE):
            for y in range(FIELD_SIZE):
                monster = self.field[x][y]
                if monster is not None:
                    cells.append((x, y, monster))
        return cells

    def players_at(self, x, y):
        """Return usernames of players standing on ``(x, y)``."""
        return [
            name
            for name, player in self.players.items()
            if player.x == x and player.y == y
        ]

    def move(self, username, dx, dy):
        """Move player and build unicast messages."""
        player = self.players[username]
        x, y = player.move(dx, dy)
        unicast = [f"Moved to ({x}, {y})"]
        monster = self.field[x][y]
        if monster:
            unicast.append(monster.encounter())
        return unicast, []

    def add_monster(self, username, hello, hp, name, x, y):
        """Place a monster and build broadcast message."""
        if name not in KNOWN_MONSTERS:
            return ["Cannot add unknown monster"], []
        self.field[x][y] = Monster(name, hello, hp)
        event = (
            "placed",
            {
                "username": username,
                "name": name,
                "hp": hp,
                "x": x,
                "y": y,
            },
        )
        return [], [event]

    def attack(self, username, monster_name, weapon_name):
        """Attack a monster and build broadcast message."""
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

        killed = monster.hitpoints == 0
        if killed:
            self.field[x][y] = None
        event = (
            "attack",
            {
                "username": username,
                "monster": monster.name,
                "weapon": weapon_name,
                "damage": damage,
                "left": monster.hitpoints,
                "killed": killed,
            },
        )
        return [], [event]

    def wander_monster(self):
        """Move one random monster one cell in a random direction."""
        cells = self.list_monster_cells()
        if not cells:
            return None

        attempts = len(cells) * len(WANDER_DIRECTIONS) * 4
        for _ in range(attempts):
            x, y, monster = random.choice(cells)
            (dx, dy), direction = random.choice(
                list(WANDER_DIRECTIONS.items())
            )
            nx = (x + dx) % FIELD_SIZE
            ny = (y + dy) % FIELD_SIZE
            occupant = self.field[nx][ny]
            if occupant is not None and occupant is not monster:
                continue

            self.field[x][y] = None
            self.field[nx][ny] = monster

            broadcast = f"{monster.name} moved one cell {direction}"
            unicast = {}
            for username in self.players_at(nx, ny):
                unicast[username] = [monster.encounter()]
            return broadcast, unicast

        return None

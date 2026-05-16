"""Game world state and rules."""

from cowsay import cowsay

from mood.common.constants import FIELD_SIZE, WEAPONS
from mood.common.monsters import KNOWN_MONSTERS, get_jgsbat


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

    def add_player(self, username):
        """Register a connected player."""
        self.players[username] = Player()

    def remove_player(self, username):
        """Remove a disconnected player."""
        self.players.pop(username, None)

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
        msg = (
            f"{username} placed monster {name} with {hp} hp "
            f"at ({x}, {y})"
        )
        return [], [msg]

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

        msg = (
            f"{username} attacked {monster.name} with {weapon_name}, "
            f"damage {damage} hp, {monster.name} has "
            f"{monster.hitpoints} hp left"
        )
        if monster.hitpoints == 0:
            self.field[x][y] = None
            msg += f", {monster.name} was killed"
        return [], [msg]

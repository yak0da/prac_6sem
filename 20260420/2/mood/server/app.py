"""Async TCP server for MOOD."""

import asyncio
import shlex

from mood.common.constants import HOST, PORT
from mood.server.game import Game, WANDER_INTERVAL_SEC
from mood.server.localize import render_event

game = Game()
clients = {}
client_locales = {}


def valid_username(username):
    """Check that username is a single non-empty token."""
    return bool(username) and " " not in username and "\n" not in username


async def send_line(writer, message):
    """Write one message line to the client."""
    if not message.endswith("\n"):
        message += "\n"
    writer.write(message.encode("utf-8"))
    await writer.drain()


def schedule_send(writer, message):
    """Schedule asynchronous send to one client."""
    asyncio.create_task(send_line(writer, message))


def localize(message, locale):
    """Translate an event tuple or pass through plain text."""
    if isinstance(message, tuple):
        return render_event(locale, message)
    return message


def schedule_broadcast(messages):
    """Schedule localized send to all clients."""
    if isinstance(messages, str):
        messages = [messages]
    for username, writer in clients.items():
        locale = client_locales.get(username)
        for message in messages:
            schedule_send(writer, localize(message, locale))


def schedule_unicast(username, messages):
    """Schedule localized send to one client by name."""
    writer = clients.get(username)
    if not writer:
        return
    locale = client_locales.get(username)
    for message in messages:
        schedule_send(writer, localize(message, locale))


def dispatch_messages(broadcast, unicast):
    """Send broadcast and per-user unicast messages asynchronously."""
    if broadcast:
        schedule_broadcast(broadcast)
    for username, messages in unicast.items():
        schedule_unicast(username, messages)


def process_command(username, data):
    """Parse and run one command line."""
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
                username,
                parts[1],
                int(parts[2]),
                parts[3],
                int(parts[4]),
                int(parts[5]),
            )
        case "attack":
            if len(parts) != 3:
                return ["Invalid arguments"], []
            return game.attack(username, parts[1], parts[2])
        case "sayall":
            if len(parts) != 2:
                return ["Invalid arguments"], []
            return [], [f"{username}: {parts[1]}"]
        case "movemonsters":
            if len(parts) != 2 or parts[1] not in ("on", "off"):
                return ["Invalid arguments"], []
            return game.set_moving_monsters(parts[1] == "on")
        case "locale":
            if len(parts) != 2:
                return ["Invalid arguments"], []
            client_locales[username] = parts[1]
            return [("locale_set", {"name": parts[1]})], []
        case _:
            return ["Invalid command"], []


async def wander_loop():
    """Move a random monster every :data:`WANDER_INTERVAL_SEC` seconds."""
    while True:
        await asyncio.sleep(WANDER_INTERVAL_SEC)
        if not game.moving_monsters:
            continue
        result = game.wander_monster()
        if result is None:
            continue
        broadcast, unicast = result
        dispatch_messages(broadcast, unicast)


async def handle_client(reader, writer):
    """Handle one connected client."""
    data = await reader.readline()
    username = data.decode("utf-8", errors="replace").strip()

    if not valid_username(username):
        await send_line(writer, "Invalid username")
        writer.close()
        await writer.wait_closed()
        return

    if username in clients:
        msg = f"Username {username} is already connected"
        await send_line(writer, msg)
        writer.close()
        await writer.wait_closed()
        return

    clients[username] = writer
    client_locales[username] = None
    game.add_player(username)

    await send_line(writer, f"Connected as {username}")
    schedule_broadcast([("joined", {"username": username})])

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            line = data.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            unicast, broadcast = process_command(username, line)
            schedule_unicast(username, unicast)
            schedule_broadcast(broadcast)
    finally:
        clients.pop(username, None)
        client_locales.pop(username, None)
        game.remove_player(username)
        schedule_broadcast([("left", {"username": username})])
        writer.close()
        await writer.wait_closed()


async def run_server(host=HOST, port=PORT):
    """Start listening for client connections."""
    asyncio.create_task(wander_loop())
    server = await asyncio.start_server(handle_client, host, port)
    async with server:
        await server.serve_forever()


def start_server(host=HOST, port=PORT):
    """Run the server until interrupted (for CLI and tests)."""
    asyncio.run(run_server(host, port))

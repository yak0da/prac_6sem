"""Async TCP server for MOOD."""

import asyncio
import shlex

from mood.common.constants import HOST, PORT
from mood.server.game import Game

game = Game()
clients = {}


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


def schedule_broadcast(message):
    """Schedule asynchronous send to all clients."""
    for writer in clients.values():
        schedule_send(writer, message)


def schedule_unicast(username, message):
    """Schedule asynchronous send to one client by name."""
    writer = clients.get(username)
    if writer:
        schedule_send(writer, message)


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
        case _:
            return ["Invalid command"], []


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


async def run_server():
    """Start listening for client connections."""
    server = await asyncio.start_server(handle_client, HOST, PORT)
    async with server:
        await server.serve_forever()

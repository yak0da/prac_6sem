"""Integration tests: client and server (including localization)."""

import multiprocessing
import socket
import time
import unittest

from mood.common.constants import HOST, PORT
from mood.server.app import start_server


class MUDTestClient:
    """Minimal TCP client for the MOOD wire protocol."""

    def __init__(self, username, host=HOST, port=PORT):
        self.sock = socket.create_connection((host, port))
        self._buffer = b""
        self.sock.sendall(f"{username}\n".encode())
        greeting = self.read_line()
        assert greeting.startswith("Connected as ")

    def send_command(self, command):
        self.sock.sendall(f"{command}\n".encode())

    def read_line(self, timeout=5.0):
        self.sock.settimeout(timeout)
        while b"\n" not in self._buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("connection closed")
            self._buffer += chunk
        line, self._buffer = self._buffer.split(b"\n", 1)
        return line.decode("utf-8", errors="replace")

    def read_line_containing(self, text, max_lines=30, timeout=5.0):
        for _ in range(max_lines):
            line = self.read_line(timeout=timeout)
            if text in line:
                return line
        raise AssertionError(f"no line containing {text!r}")

    def close(self):
        self.sock.close()


class TestServerCommands(unittest.TestCase):
    """Client+server tests against a background server process."""

    @classmethod
    def setUpClass(cls):
        cls.server_proc = multiprocessing.Process(
            target=start_server,
            kwargs={"host": HOST, "port": PORT},
        )
        cls.server_proc.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server_proc.terminate()
        cls.server_proc.join(timeout=3)

    def setUp(self):
        name = f"test_{self.id().split('.')[-1]}"
        self.client = MUDTestClient(name)
        self.client.send_command("movemonsters off")
        self.client.read_line_containing("Moving monsters: off")

    def tearDown(self):
        self.client.close()

    def test_locale_russian(self):
        """Server returns Russian text after locale is set."""
        self.client.send_command("locale ru_RU.UTF-8")
        line = self.client.read_line()
        self.assertIn("Установлена локаль", line)
        self.assertIn("ru_RU.UTF-8", line)

    def test_add_monster(self):
        self.client.send_command('addmon "Hi" 10 dragon 1 0')
        line = self.client.read_line_containing("placed monster dragon")
        self.assertIn("10 hp", line)
        self.assertIn("(1, 0)", line)

    def test_monster_encounter(self):
        self.client.send_command('addmon "Hello" 10 dragon 1 0')
        self.client.read_line_containing("placed monster dragon")
        self.client.send_command("move 1 0")
        self.client.read_line_containing("Moved to (1, 0)")
        greeting = self.client.read_line_containing("Hello", max_lines=30)
        self.assertIn("Hello", greeting)

    def test_attack_monster(self):
        self.client.send_command('addmon "Roar" 15 dragon 1 0')
        self.client.read_line_containing("placed monster dragon")
        self.client.send_command("move 1 0")
        self.client.read_line_containing("Moved to (1, 0)")
        self.client.read_line_containing("Roar", max_lines=30)
        self.client.send_command("attack dragon sword")
        line = self.client.read_line_containing("attacked dragon")
        self.assertIn("sword", line)
        self.assertIn("damage", line)


if __name__ == "__main__":
    unittest.main()

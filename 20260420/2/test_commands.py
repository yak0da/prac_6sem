import io
import shlex
import unittest
from unittest.mock import MagicMock, patch

from mood.client.shell import MUD_SH


def sent_messages(sock):
    lines = []
    for call in sock.sendall.call_args_list:
        lines.append(call[0][0].decode("utf-8"))
    return lines


class TestMoveCommands(unittest.TestCase):

    def setUp(self):
        self.sock = MagicMock()
        self.mud = MUD_SH(self.sock)

    def test_up_to_protocol(self):
        self.mud.onecmd("up")
        self.assertEqual(sent_messages(self.sock), ["move 0 -1\n"])

    def test_right_to_protocol(self):
        self.mud.onecmd("right")
        self.assertEqual(sent_messages(self.sock), ["move 1 0\n"])


class TestAddmonCommand(unittest.TestCase):

    def setUp(self):
        self.sock = MagicMock()
        self.mud = MUD_SH(self.sock)

    def test_addmon_coords_1_2(self):
        hello = "Hi there"
        self.mud.onecmd(
            f'addmon dragon hello "{hello}" hp 10 coords 1 2'
        )
        expected = (
            f"addmon {shlex.quote(hello)} 10 dragon 1 2\n"
        )
        self.assertEqual(sent_messages(self.sock), [expected])

    def test_addmon_coords_3_4(self):
        self.mud.onecmd("addmon bunny hello Hop hp 5 coords 3 4")
        self.assertEqual(
            sent_messages(self.sock),
            ["addmon Hop 5 bunny 3 4\n"],
        )

    def test_unknown_monster_not_sent(self):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            self.mud.onecmd("addmon foo hello x hp 1 coords 0 0")
        self.sock.sendall.assert_not_called()
        self.assertIn("Cannot add unknown monster", out.getvalue())

    def test_invalid_arguments_not_sent(self):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            self.mud.onecmd("addmon dragon hello only")
        self.sock.sendall.assert_not_called()
        self.assertIn("Invalid arguments", out.getvalue())


class TestInputSequence(unittest.TestCase):

    def test_sequence_via_cmdloop(self):
        sock = MagicMock()
        mud = MUD_SH(sock)
        mud.use_rawinput = True
        inputs = iter(["up", "right", "EOF"])

        def mock_input(_prompt=""):
            line = next(inputs)
            if line == "EOF":
                raise EOFError
            return line

        with patch("builtins.input", mock_input):
            mud.cmdloop()

        self.assertEqual(
            sent_messages(sock),
            ["move 0 -1\n", "move 1 0\n"],
        )


if __name__ == "__main__":
    unittest.main()

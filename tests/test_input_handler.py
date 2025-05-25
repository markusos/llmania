import curses  # For curses.error and other constants
import unittest
from unittest.mock import MagicMock, patch

# Assuming src is in PYTHONPATH or tests are run in a way that src can be imported
from src.input_handler import InputHandler
from src.parser import Parser  # Parser is needed for instantiation, will be mocked


class TestInputHandler(unittest.TestCase):
    def setUp(self):
        # Mock stdscr
        self.mock_stdscr = MagicMock()
        self.mock_stdscr.getkey = MagicMock()  # Mock getkey specifically

        # Mock Parser
        self.mock_parser = MagicMock(spec=Parser)
        self.mock_parser.parse_command = MagicMock(
            return_value=("parsed_command", "arg")
        )

        # Mock curses.curs_set globally via patch, as it's a global function
        self.curs_set_patcher = patch("curses.curs_set")
        self.mock_curs_set = self.curs_set_patcher.start()
        self.addCleanup(
            self.curs_set_patcher.stop
        )  # Ensure patch is stopped after tests

        # Instantiate InputHandler
        self.input_handler = InputHandler(self.mock_stdscr, self.mock_parser)

    def test_initial_state(self):
        self.assertEqual(self.input_handler.get_input_mode(), "movement")
        self.assertEqual(self.input_handler.get_command_buffer(), "")
        # curses.curs_set called to hide cursor in movement mode if constructor sets it.
        # Current InputHandler constructor does not explicitly call curs_set.
        # It's usually called when a key is processed or mode changes.

    def test_movement_mode_arrow_keys(self):
        key_map = {
            "KEY_UP": ("move", "north"),
            "w": ("move", "north"),
            "W": ("move", "north"),
            "KEY_DOWN": ("move", "south"),
            "s": ("move", "south"),
            "S": ("move", "south"),
            "KEY_LEFT": ("move", "west"),
            "a": ("move", "west"),
            "A": ("move", "west"),
            "KEY_RIGHT": ("move", "east"),
            "d": ("move", "east"),
            "D": ("move", "east"),
        }
        for key_name, expected_command in key_map.items():
            with self.subTest(key=key_name):
                self.input_handler.input_mode = "movement"  # Ensure mode
                self.mock_stdscr.getkey.return_value = key_name
                command = self.input_handler.handle_input_and_get_command()
                self.assertEqual(command, expected_command)
                self.mock_curs_set.assert_called_with(0)  # Cursor hidden in movement

    def test_movement_to_command_mode_with_tilde(self):
        self.input_handler.input_mode = "movement"
        self.mock_stdscr.getkey.return_value = "`"
        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)  # Mode switch doesn't return a command
        self.assertEqual(self.input_handler.get_input_mode(), "command")
        self.assertEqual(self.input_handler.get_command_buffer(), "")
        self.mock_curs_set.assert_called_with(1)  # Cursor visible in command mode

    def test_command_mode_submit_command(self):
        self.input_handler.input_mode = "command"
        self.input_handler.current_command_buffer = "test cmd"
        self.mock_stdscr.getkey.return_value = "\n"  # Enter key

        # Expected return from parser
        parsed_cmd_mock = ("parsed_cmd", "from_parser")
        self.mock_parser.parse_command.return_value = parsed_cmd_mock

        command = self.input_handler.handle_input_and_get_command()

        self.assertEqual(command, parsed_cmd_mock)
        self.mock_parser.parse_command.assert_called_once_with("test cmd")
        self.assertEqual(self.input_handler.get_input_mode(), "movement")
        self.assertEqual(self.input_handler.get_command_buffer(), "")
        self.mock_curs_set.assert_called_with(
            0
        )  # Cursor hidden after returning to movement

    def test_command_mode_submit_empty_command(self):
        self.input_handler.input_mode = "command"
        self.input_handler.current_command_buffer = ""  # Empty buffer
        self.mock_stdscr.getkey.return_value = "\n"  # Enter key

        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)  # No command parsed or returned
        self.mock_parser.parse_command.assert_not_called()  # Parser not called
        self.assertEqual(
            self.input_handler.get_input_mode(), "movement"
        )  # Switch to movement
        self.mock_curs_set.assert_called_with(0)

    def test_command_mode_backspace(self):
        self.input_handler.input_mode = "command"
        self.input_handler.current_command_buffer = "abc"
        self.mock_stdscr.getkey.return_value = "KEY_BACKSPACE"

        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)
        self.assertEqual(self.input_handler.get_command_buffer(), "ab")
        self.mock_curs_set.assert_called_with(1)  # Cursor remains visible

    def test_command_mode_escape_key(self):
        self.input_handler.input_mode = "command"
        self.input_handler.current_command_buffer = "some text"
        self.mock_stdscr.getkey.return_value = "\x1b"  # Escape key

        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)
        self.assertEqual(self.input_handler.get_input_mode(), "movement")
        self.assertEqual(self.input_handler.get_command_buffer(), "")
        self.mock_curs_set.assert_called_with(0)

    def test_command_mode_tide_key_empty_buffer(self):
        self.input_handler.input_mode = "command"
        self.input_handler.current_command_buffer = ""
        self.mock_stdscr.getkey.return_value = "`"

        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)
        self.assertEqual(self.input_handler.get_input_mode(), "movement")
        self.mock_curs_set.assert_called_with(0)

    def test_command_mode_tilde_key_non_empty_buffer(self):
        self.input_handler.input_mode = "command"
        self.input_handler.current_command_buffer = "test"
        self.mock_stdscr.getkey.return_value = "`"

        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)
        self.assertEqual(
            self.input_handler.get_input_mode(), "command"
        )  # Stays in command mode
        self.assertEqual(
            self.input_handler.get_command_buffer(), "test`"
        )  # '`' appended
        self.mock_curs_set.assert_called_with(1)

    def test_command_mode_add_character_to_buffer(self):
        self.input_handler.input_mode = "command"
        self.input_handler.current_command_buffer = "ab"
        self.mock_stdscr.getkey.return_value = "c"

        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)
        self.assertEqual(self.input_handler.get_command_buffer(), "abc")
        self.mock_curs_set.assert_called_with(1)

    def test_getkey_raises_curses_error(self):
        self.input_handler.input_mode = "movement"
        self.mock_stdscr.getkey.side_effect = curses.error("test error")
        command = self.input_handler.handle_input_and_get_command()
        self.assertIsNone(command)

    def test_resize_event_movement_mode(self):
        self.input_handler.input_mode = "movement"
        self.mock_stdscr.getkey.return_value = "KEY_RESIZE"
        command = self.input_handler.handle_input_and_get_command()
        self.assertEqual(command, ("resize_event", None))
        self.mock_stdscr.clear.assert_called_once()  # Check if clear is called

    def test_resize_event_command_mode(self):
        self.input_handler.input_mode = "command"
        self.mock_stdscr.getkey.return_value = "KEY_RESIZE"
        command = self.input_handler.handle_input_and_get_command()
        self.assertEqual(command, ("resize_event", None))
        self.mock_stdscr.clear.assert_called_once()


if __name__ == "__main__":
    unittest.main()

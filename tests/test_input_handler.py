import unittest
from unittest.mock import MagicMock, patch

# Assuming src is in PYTHONPATH or tests are run in a way that src can be imported
from src.input_handler import InputHandler
from src.input_mode import InputMode
from src.parser import Parser  # Parser is needed for instantiation, will be mocked


class TestInputHandler(unittest.TestCase):
    def setUp(self):
        self.mock_stdscr = MagicMock()
        self.mock_parser = MagicMock(spec=Parser)
        self.input_handler = InputHandler(self.mock_stdscr, self.mock_parser)
        self.curs_set_patcher = patch("curses.curs_set")
        self.mock_curs_set = self.curs_set_patcher.start()
        self.addCleanup(self.curs_set_patcher.stop)

    def test_handle_input_movement_mode(self):
        self.mock_stdscr.getkey.return_value = "w"
        command = self.input_handler.handle_input_and_get_command(InputMode.MOVEMENT)
        self.assertEqual(command, ("move", "north"))

    def test_handle_input_command_mode(self):
        self.input_handler.current_command_buffer = "take"
        self.mock_stdscr.getkey.return_value = "\n"
        self.mock_parser.parse_command.return_value = ("take", None)
        command = self.input_handler.handle_input_and_get_command(InputMode.COMMAND)
        self.assertEqual(command, ("take", None))
        self.assertEqual(self.input_handler.current_command_buffer, "")

    def test_handle_input_inventory_mode(self):
        self.mock_stdscr.getkey.return_value = "~"
        command = self.input_handler.handle_input_and_get_command(InputMode.INVENTORY)
        self.assertEqual(command, "inventory")

    def test_switch_to_command_mode(self):
        self.mock_stdscr.getkey.return_value = "`"
        command = self.input_handler.handle_input_and_get_command(InputMode.MOVEMENT)
        self.assertEqual(command, "command_mode")

    def test_switch_to_movement_mode(self):
        self.mock_stdscr.getkey.return_value = "\x1b"  # Escape
        command = self.input_handler.handle_input_and_get_command(InputMode.COMMAND)
        self.assertEqual(command, "movement_mode")


if __name__ == "__main__":
    unittest.main()

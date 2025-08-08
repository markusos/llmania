import curses
from typing import Optional

from src.parser import Parser


class InputHandler:
    """
    Manages player input, switching between movement and command input modes.
    It captures key presses, processes them according to the current mode,
    and uses a Parser to interpret commands.
    """

    def __init__(
        self, stdscr: Optional[object], parser: Parser, debug_mode: bool = False
    ):
        """
        Initializes the InputHandler.
        """
        self.stdscr = stdscr
        self.parser = parser
        self.current_command_buffer = ""
        self.debug_mode = debug_mode

    def handle_input_and_get_command(
        self, input_mode: str
    ) -> tuple[str, str | None] | None | str:
        """
        Captures a key press and processes it based on the current input mode.
        """
        if self.debug_mode:
            try:
                command_line = input("> ")
                if not command_line:
                    return None
                return self.parser.parse_command(command_line)
            except EOFError:
                return "NO_COMMAND"

        if not self.stdscr:
            return None

        try:
            key = self.stdscr.getkey()
        except curses.error:
            return None

        if input_mode == "inventory":
            if key in ["`", "~", "i", "I"]:
                return "inventory"  # Special command to toggle inventory
            return None

        if input_mode == "movement":
            curses.curs_set(0)
            if key in ["KEY_UP", "w", "W"]:
                return ("move", "north")
            elif key in ["KEY_DOWN", "s", "S"]:
                return ("move", "south")
            elif key in ["KEY_LEFT", "a", "A"]:
                return ("move", "west")
            elif key in ["KEY_RIGHT", "d", "D"]:
                return ("move", "east")
            elif key in ["`", "~"]:
                self.current_command_buffer = ""
                curses.curs_set(1)
                return "command_mode"
            elif key == "KEY_RESIZE":
                self.stdscr.clear()
                return ("resize_event", None)

        elif input_mode == "command":
            curses.curs_set(1)
            if key in ["\n", "\r", "KEY_ENTER"]:
                if self.current_command_buffer:
                    parsed_command = self.parser.parse_command(
                        self.current_command_buffer
                    )
                    self.current_command_buffer = ""
                    curses.curs_set(0)
                    return parsed_command
                else:
                    curses.curs_set(0)
                    return "movement_mode"
            elif key in ["KEY_BACKSPACE", "\b", "\x7f"]:
                self.current_command_buffer = self.current_command_buffer[:-1]
            elif key == "\x1b":
                self.current_command_buffer = ""
                curses.curs_set(0)
                return "movement_mode"
            elif key in ["`", "~"] and not self.current_command_buffer:
                curses.curs_set(0)
                return "movement_mode"
            elif key == "KEY_RESIZE":
                self.stdscr.clear()
                return ("resize_event", None)
            elif isinstance(key, str) and key.isprintable() and len(key) == 1:
                self.current_command_buffer += key

        return None

    def get_command_buffer(self) -> str:
        """
        Returns the current content of the command input buffer.
        """
        return self.current_command_buffer

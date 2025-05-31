import curses

from parser import Parser


class InputHandler:
    """
    Manages player input, switching between movement and command input modes.
    It captures key presses, processes them according to the current mode,
    and uses a Parser to interpret commands.
    """

    def __init__(self, stdscr, parser: Parser):
        """
        Initializes the InputHandler.

        Args:
            stdscr: The curses standard screen object for input.
            parser: An instance of the Parser class to parse command strings.
        """
        self.stdscr = stdscr
        self.parser = parser
        self.input_mode = "movement"  # Can be "movement" or "command"
        self.current_command_buffer = ""  # Stores typed characters in command mode

    def handle_input_and_get_command(self) -> tuple[str, str | None] | None:
        """
        Captures a key press and processes it based on the current input mode.

        In "movement" mode, it translates keys (arrow keys, WASD)
        into movement commands. The tilde key (`) switches to "command" mode.

        In "command" mode, it accumulates characters into a buffer. Enter key
        parses the buffer. Escape or tilde (on empty buffer) switches to
        "movement" mode. Backspace deletes characters.

        Returns:
            A tuple (verb, argument) if a command is fully entered or a movement key
            is pressed, e.g., ("move", "north") or ("take", "potion").
            Returns ("resize_event", None) if a resize event is detected.
            Returns None if input does not result in a complete command yet (e.g.,
            typing in command mode, or non-actionable key press).
        """
        try:
            key = self.stdscr.getkey()  # Get a key press
        except curses.error:
            # This can happen if stdscr.nodelay(True) is set and no key is pressed.
            # For this game, getkey() is blocking, so this might be less common
            # unless specific curses configurations are made.
            return None  # No input or non-blocking timeout

        if self.input_mode == "movement":
            curses.curs_set(0)  # Hide cursor in movement mode
            if key in ["KEY_UP", "w", "W"]:
                return ("move", "north")
            elif key in ["KEY_DOWN", "s", "S"]:
                return ("move", "south")
            elif key in ["KEY_LEFT", "a", "A"]:
                return ("move", "west")
            elif key in ["KEY_RIGHT", "d", "D"]:
                return ("move", "east")
            elif key in ["`", "~"]:  # Tilde key to switch to command mode
                self.input_mode = "command"
                self.current_command_buffer = ""
                curses.curs_set(1)  # Show cursor in command mode
                return None  # Mode switch, no command generated yet
            elif key == "KEY_RESIZE":
                # Handle terminal resize events. Renderer might need to adjust.
                self.stdscr.clear()  # Example: clear screen on resize
                # GameEngine or Renderer should ideally handle the full refresh logic.
                return ("resize_event", None)

        elif self.input_mode == "command":
            curses.curs_set(1)  # Ensure cursor is visible
            if key in ["\n", "\r", "KEY_ENTER"]:  # Enter key pressed
                if self.current_command_buffer:
                    # Parse the command from the buffer
                    parsed_command = self.parser.parse_command(
                        self.current_command_buffer
                    )
                    self.current_command_buffer = ""  # Clear buffer
                    self.input_mode = "movement"  # Switch back to movement mode
                    curses.curs_set(0)  # Hide cursor
                    return parsed_command
                else:  # Empty command buffer, just switch to movement mode
                    self.input_mode = "movement"
                    curses.curs_set(0)
                    return None
            elif key in ["KEY_BACKSPACE", "\b", "\x7f"]:  # Backspace variants
                self.current_command_buffer = self.current_command_buffer[:-1]
                return None  # Buffer changed, no command generated yet
            elif key == "\x1b":  # Escape key
                self.current_command_buffer = ""  # Clear buffer
                self.input_mode = "movement"  # Switch to movement mode
                curses.curs_set(0)
                return None
            elif (
                key in ["`", "~"] and not self.current_command_buffer
            ):  # Tilde on empty buffer
                self.input_mode = "movement"  # Switch to movement mode
                curses.curs_set(0)
                return None
            elif key == "KEY_RESIZE":
                self.stdscr.clear()
                return ("resize_event", None)
            elif isinstance(key, str) and key.isprintable() and len(key) == 1:
                # Append printable characters to the command buffer
                self.current_command_buffer += key
                return None  # Buffer changed, no command generated yet

        return None  # Default: key did not result in an action or full command

    def get_input_mode(self) -> str:
        """
        Returns the current input mode.

        Returns:
            str: "movement" or "command".
        """
        return self.input_mode

    def get_command_buffer(self) -> str:
        """
        Returns the current content of the command input buffer.

        Returns:
            str: The characters currently typed in command mode.
        """
        return self.current_command_buffer

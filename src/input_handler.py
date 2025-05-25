import curses

from src.parser import Parser


class InputHandler:
    def __init__(self, stdscr, parser: Parser):
        self.stdscr = stdscr
        self.parser = parser
        self.input_mode = "movement"  # or "command"
        self.current_command_buffer = ""

    def handle_input_and_get_command(self):
        try:
            key = self.stdscr.getkey()
        except curses.error:
            return None  # No input or non-blocking timeout

        if self.input_mode == "movement":
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
                self.input_mode = "command"
                self.current_command_buffer = ""
                curses.curs_set(1)
                return None
            elif key == "KEY_RESIZE":
                # In a real application, you might want to trigger a screen refresh
                # or recalculate layout. For now, just acknowledge.
                self.stdscr.clear()  # Example action
                return ("resize_event", None)

        elif self.input_mode == "command":
            curses.curs_set(1)
            if key in ["\n", "\r", "KEY_ENTER"]:  # curses.KEY_ENTER might be an int
                if self.current_command_buffer:
                    parsed_command = self.parser.parse_command(
                        self.current_command_buffer
                    )  # Changed parse to parse_command
                    self.current_command_buffer = ""
                    self.input_mode = "movement"
                    curses.curs_set(0)
                    return parsed_command
                else:  # Empty command, switch to movement mode
                    self.input_mode = "movement"
                    curses.curs_set(0)
                    return None
            elif key in [
                "KEY_BACKSPACE",
                "\b",
                "\x7f",
            ]:  # \b for terminals, \x7f for others
                self.current_command_buffer = self.current_command_buffer[:-1]
                return None
            elif key == "\x1b":  # Escape key
                self.current_command_buffer = ""
                self.input_mode = "movement"
                curses.curs_set(0)
                return None
            elif (
                key in ["`", "~"] and not self.current_command_buffer
            ):  # tilde key to exit command mode if buffer is empty
                self.input_mode = "movement"
                curses.curs_set(0)
                return None
            elif key == "KEY_RESIZE":
                # In a real application, you might want to trigger a screen refresh
                # or recalculate layout. For now, just acknowledge.
                self.stdscr.clear()  # Example action
                return ("resize_event", None)
            elif isinstance(key, str) and key.isprintable() and len(key) == 1:
                self.current_command_buffer += key
                return None

        return None  # Default fall-through

    def get_input_mode(self):
        return self.input_mode

    def get_command_buffer(self):
        return self.current_command_buffer

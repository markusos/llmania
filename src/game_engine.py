import curses

from src.parser import Parser
from src.player import Player
from src.world_generator import WorldGenerator


class GameEngine:
    def __init__(self, map_width: int = 20, map_height: int = 10):
        self.world_generator = WorldGenerator()
        self.parser = Parser()
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        curses.curs_set(0)  # Hide cursor initially
        self.input_mode = "movement"  # or "command"
        self.current_command_buffer = ""
        self.world_map, player_start_pos, self.win_pos = (
            self.world_generator.generate_map(map_width, map_height, seed=None)
        )
        self.player = Player(x=player_start_pos[0], y=player_start_pos[1], health=20)
        self.game_over = False
        self.message_log = []

    def handle_input_and_get_command(self) -> tuple[str, str | None] | None:
        try:
            key = self.stdscr.getkey()
        except curses.error:
            return None  # e.g., if a timeout was set for getkey and no input occurred

        command_tuple = None
        if self.input_mode == "movement":
            self.stdscr.curs_set(0)
            if key == "KEY_UP" or key == "w" or key == "W":
                command_tuple = ("move", "north")
            elif key == "KEY_DOWN" or key == "s" or key == "S":
                command_tuple = ("move", "south")
            elif key == "KEY_LEFT" or key == "a" or key == "A":
                command_tuple = ("move", "west")
            elif key == "KEY_RIGHT" or key == "d" or key == "D":
                command_tuple = ("move", "east")
            elif (
                key == "q" or key == "Q"
            ):  # 'q' in movement mode switches to command mode
                self.input_mode = "command"
                self.current_command_buffer = ""
                self.stdscr.curs_set(1)  # Show cursor
            return command_tuple

        elif self.input_mode == "command":
            self.stdscr.curs_set(1)
            # Check for special keys first
            if key == "\n" or key == curses.KEY_ENTER:
                command_to_parse = self.current_command_buffer
                self.current_command_buffer = ""
                self.input_mode = "movement"
                self.stdscr.curs_set(0)
                command_tuple = self.parser.parse_command(command_to_parse)
                return command_tuple # Return parsed command
            elif key == "KEY_BACKSPACE" or key == "\x08" or key == "\x7f":
                self.current_command_buffer = self.current_command_buffer[:-1]
            elif key == "\x1b":  # Escape key
                self.current_command_buffer = ""
                self.input_mode = "movement"
                self.stdscr.curs_set(0)
            elif key == "q" or key == "Q":  # 'q' or 'Q' to exit command mode
                self.current_command_buffer = ""
                self.input_mode = "movement"
                self.stdscr.curs_set(0)
            elif key == "KEY_RESIZE":  # Handle resize event
                self.stdscr.clear()
                # The next render_map call will redraw based on new screen size
            elif isinstance(key, str) and len(key) == 1 and key.isprintable():
                self.current_command_buffer += key
            return None  # Command not yet submitted or mode switched / unhandled key

        return None # Should only be reached if input_mode is neither "movement" nor "command"

    def render_map(self):
        self.stdscr.clear()
        max_y_map = min(self.world_map.height, curses.LINES - 4)
        max_x_map = min(self.world_map.width, curses.COLS - 1)

        for y_map in range(max_y_map):
            for x_map in range(max_x_map):
                char_to_draw = ""
                if x_map == self.player.x and y_map == self.player.y:
                    char_to_draw = "@"
                else:
                    tile = self.world_map.get_tile(x_map, y_map)
                    char_to_draw = tile.display_char() if tile else "?"
                try:
                    self.stdscr.addstr(y_map, x_map, char_to_draw)
                except curses.error:
                    pass

        hp_line_y = max_y_map
        if hp_line_y < curses.LINES:
            hp_text = f"HP: {self.player.health}"
            try:
                self.stdscr.addstr(hp_line_y, 0, hp_text)
            except curses.error:
                pass
        else:
            hp_line_y = curses.LINES - 1

        mode_line_y = hp_line_y + 1
        if mode_line_y < curses.LINES:
            mode_text = f"MODE: {self.input_mode.upper()}"
            try:
                self.stdscr.addstr(mode_line_y, 0, mode_text)
            except curses.error:
                pass
        else:
            mode_line_y = curses.LINES - 1

        message_start_y = mode_line_y + 1
        if self.input_mode == "command":
            if mode_line_y + 1 < curses.LINES:
                prompt_text = f"> {self.current_command_buffer}"
                try:
                    self.stdscr.addstr(mode_line_y + 1, 0, prompt_text)
                    message_start_y = mode_line_y + 2
                except curses.error:
                    pass

        num_messages_to_display = 5
        available_lines_for_messages = curses.LINES - message_start_y
        if available_lines_for_messages < 0:
            available_lines_for_messages = 0
        num_messages_to_display = min(
            num_messages_to_display, available_lines_for_messages
        )
        start_index = max(0, len(self.message_log) - num_messages_to_display)
        last_messages = self.message_log[start_index:]

        for i, message in enumerate(last_messages):
            current_message_y = message_start_y + i
            if current_message_y < curses.LINES:
                if len(message) >= curses.COLS:
                    message = message[: curses.COLS - 1]
                try:
                    self.stdscr.addstr(current_message_y, 0, message)
                except curses.error:
                    break
            else:
                break
        self.stdscr.refresh()

    # Renamed from process_command
    def process_command_tuple(
        self, parsed_command_tuple: tuple[str, str | None] | None
    ):
        self.message_log.clear()
        if self.game_over:
            self.message_log.append("The game is over.")
            return

        if parsed_command_tuple is None:
            self.message_log.append("Unknown command.")
            return

        verb, argument = parsed_command_tuple
        if verb == "move":
            dx, dy = 0, 0
            if argument == "north":
                dy = -1
            elif argument == "south":
                dy = 1
            elif argument == "east":
                dx = 1
            elif argument == "west":
                dx = -1

            new_x, new_y = self.player.x + dx, self.player.y + dy
            if self.world_map.is_valid_move(new_x, new_y):
                target_tile = self.world_map.get_tile(new_x, new_y)
                if target_tile and target_tile.monster:
                    self.message_log.append(
                        f"You bump into a {target_tile.monster.name}!"
                    )
                else:
                    self.player.move(dx, dy)
                    self.message_log.append(f"You move {argument}.")
                    if (self.player.x, self.player.y) == self.win_pos:
                        win_tile = self.world_map.get_tile(
                            self.win_pos[0], self.win_pos[1]
                        )
                        if (
                            win_tile
                            and win_tile.item
                            and win_tile.item.properties.get("type") == "quest"
                        ):
                            self.message_log.append(
                                "You reached the Amulet of Yendor's location!"
                            )
            else:
                self.message_log.append("You can't move there.")

        elif verb == "take":
            tile = self.world_map.get_tile(self.player.x, self.player.y)
            if (
                tile
                and tile.item
                and (argument is None or tile.item.name.lower() == argument.lower())
            ):
                item_taken = self.world_map.remove_item(self.player.x, self.player.y)
                if item_taken:
                    self.player.take_item(item_taken)
                    self.message_log.append(f"You take the {item_taken.name}.")
                    if (
                        self.player.x,
                        self.player.y,
                    ) == self.win_pos and item_taken.properties.get("type") == "quest":
                        self.message_log.append(
                            "You picked up the Amulet of Yendor! You win!"
                        )
                        self.game_over = True
                else:
                    self.message_log.append("Error: Tried to take item but failed.")
            else:
                self.message_log.append(
                    f"There is no {argument} here to take."
                    if argument
                    else "Nothing here to take or item name mismatch."
                )

        elif verb == "drop":
            if argument is None:
                self.message_log.append("What do you want to drop?")
                return
            dropped_item = self.player.drop_item(argument)
            if dropped_item:
                current_tile = self.world_map.get_tile(self.player.x, self.player.y)
                if current_tile and current_tile.item is None:
                    self.world_map.place_item(
                        dropped_item, self.player.x, self.player.y
                    )
                    self.message_log.append(f"You drop the {dropped_item.name}.")
                else:
                    self.player.take_item(dropped_item)
                    self.message_log.append(
                        f"You can't drop {dropped_item.name} here, space occupied."
                    )
            else:
                self.message_log.append(f"You don't have a {argument} to drop.")

        elif verb == "use":
            if argument is None:
                self.message_log.append("What do you want to use?")
                return
            message = self.player.use_item(argument)
            self.message_log.append(message)

        elif verb == "attack":
            tile = self.world_map.get_tile(self.player.x, self.player.y)
            if tile and tile.monster:
                if argument is None or tile.monster.name.lower() == argument.lower():
                    monster = tile.monster
                    damage_dealt = self.player.attack_monster(monster)
                    self.message_log.append(
                        f"You attack the {monster.name} for {damage_dealt} damage."
                    )
                    if monster.health <= 0:
                        self.world_map.remove_monster(self.player.x, self.player.y)
                        self.message_log.append(f"You defeated the {monster.name}!")
                    else:
                        damage_taken = monster.attack(self.player)
                        self.message_log.append(
                            f"The {monster.name} attacks you for {damage_taken} damage."
                        )
                        if self.player.health <= 0:
                            self.message_log.append(
                                "You have been defeated. Game Over."
                            )
                            self.game_over = True
                else:
                    self.message_log.append(
                        f"There is no monster named {argument} here."
                    )
            else:
                self.message_log.append("There is no monster here to attack.")

        elif verb == "inventory":
            if self.player.inventory:
                item_names = ", ".join([item.name for item in self.player.inventory])
                self.message_log.append(f"Inventory: {item_names}")
            else:
                self.message_log.append("Your inventory is empty.")

        elif verb == "look":
            tile = self.world_map.get_tile(self.player.x, self.player.y)
            description = f"You are at ({self.player.x}, {self.player.y})."
            self.message_log.append(description)
            if tile:
                if tile.item:
                    self.message_log.append(f"You see a {tile.item.name} here.")
                if tile.monster:
                    self.message_log.append(f"There is a {tile.monster.name} here!")
                if not tile.item and not tile.monster:
                    self.message_log.append("The area is clear.")

        elif verb == "quit":  # This is if "quit" is typed as a command
            self.message_log.append("Quitting game.")
            self.game_over = True

    def run(self):
        try:
            self.render_map()
            while not self.game_over:
                parsed_command_output = self.handle_input_and_get_command()
                if parsed_command_output:
                    self.process_command_tuple(parsed_command_output)
                self.render_map()

            self.render_map()
            if self.game_over:
                curses.napms(2000)
        finally:
            if hasattr(self, "stdscr"):
                self.stdscr.keypad(False)
                curses.echo()
                curses.nocbreak()
                curses.endwin()

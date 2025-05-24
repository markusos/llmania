import curses

# Assuming these are first-party imports
from src.parser import Parser
from src.player import Player
from src.tile import TILE_SYMBOLS
from src.world_generator import WorldGenerator

# Monster class is forward-declared as a string literal in type hints


class GameEngine:
    def __init__(
        self, map_width: int = 20, map_height: int = 10, debug_mode: bool = False
    ):
        self.world_generator = WorldGenerator()
        self.parser = Parser()
        self.debug_mode = debug_mode
        self.PLAYER_SYMBOL = "🧑"

        if not self.debug_mode:
            self.stdscr = curses.initscr()
            curses.start_color()
            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(True)
            curses.curs_set(0)

            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.FLOOR_COLOR_PAIR = 1
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            self.WALL_COLOR_PAIR = 2
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.PLAYER_COLOR_PAIR = 3
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.MONSTER_COLOR_PAIR = 4
            curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.ITEM_COLOR_PAIR = 5
        else:
            self.stdscr = None
            self.FLOOR_COLOR_PAIR = 0
            self.WALL_COLOR_PAIR = 0
            self.PLAYER_COLOR_PAIR = 0
            self.MONSTER_COLOR_PAIR = 0
            self.ITEM_COLOR_PAIR = 0

        self.input_mode = "movement"
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
            return None

        command_tuple = None
        if self.input_mode == "movement":
            curses.curs_set(0)
            if key == "KEY_UP" or key == "w" or key == "W":
                command_tuple = ("move", "north")
            elif key == "KEY_DOWN" or key == "s" or key == "S":
                command_tuple = ("move", "south")
            elif key == "KEY_LEFT" or key == "a" or key == "A":
                command_tuple = ("move", "west")
            elif key == "KEY_RIGHT" or key == "d" or key == "D":
                command_tuple = ("move", "east")
            elif key == "q" or key == "Q":
                self.input_mode = "command"
                self.current_command_buffer = ""
                curses.curs_set(1)
            return command_tuple

        elif self.input_mode == "command":
            curses.curs_set(1)
            if key == "\n" or key == curses.KEY_ENTER:
                command_to_parse = self.current_command_buffer
                self.current_command_buffer = ""
                self.input_mode = "movement"
                curses.curs_set(0)
                command_tuple = self.parser.parse_command(command_to_parse)
                return command_tuple
            elif key == "KEY_BACKSPACE" or key == "\x08" or key == "\x7f":
                self.current_command_buffer = self.current_command_buffer[:-1]
            elif key == "\x1b":  # Escape key
                self.current_command_buffer = ""
                self.input_mode = "movement"
                curses.curs_set(0)
            elif key == "q" or key == "Q":
                self.current_command_buffer = ""
                self.input_mode = "movement"
                curses.curs_set(0)
            elif key == "KEY_RESIZE":
                self.stdscr.clear()
            elif isinstance(key, str) and len(key) == 1 and key.isprintable():
                self.current_command_buffer += key
            return None
        return None

    def render_map(self, debug_render_to_list=False):
        if debug_render_to_list:
            output_buffer = []
            # For debug rendering, use full map height and width
            max_y_map = self.world_map.height
            max_x_map = self.world_map.width

            for y_map in range(max_y_map):
                row_str = ""
                for x_map in range(max_x_map):
                    char_to_draw = ""
                    if x_map == self.player.x and y_map == self.player.y:
                        char_to_draw = self.PLAYER_SYMBOL  # No padding
                    else:
                        tile = self.world_map.get_tile(x_tile_idx, y_tile_idx)
                        if tile:
                            # tile.get_display_info() returns (symbol, type_string)
                            symbol, _ = tile.get_display_info()
                            char_to_draw = symbol  # No padding
                        else:
                            char_to_draw = TILE_SYMBOLS["unknown"]
                    row_str += char_to_draw
                output_buffer.append(row_str)

            # UI elements
            output_buffer.append(f"HP: {self.player.health}")
            output_buffer.append(f"MODE: {self.input_mode.upper()}")
            if self.input_mode == "command":
                output_buffer.append(f"> {self.current_command_buffer}")
            for message in self.message_log:
                output_buffer.append(message)
            return output_buffer

        # Main rendering path (reverted to single characters)
        if self.debug_mode:  # Should not happen if not debug_render_to_list
            print(
                "Error: Curses rendering called in debug mode "
                "without debug_render_to_list=True."
            )
            return

        self.stdscr.clear()
        UI_LINES_BUFFER = 4  # Number of lines for UI

        max_y_curses_rows = min(self.world_map.height, curses.LINES - UI_LINES_BUFFER)
        max_x_curses_cols = curses.COLS - 1

        for y_map_idx in range(max_y_curses_rows):
            current_screen_x = 0
            for x_tile_idx in range(self.world_map.width):
                if current_screen_x >= max_x_curses_cols:
                    break

                char_to_draw = ""
                color_attribute = curses.color_pair(0)  # Default color

                if x_tile_idx == self.player.x and y_map_idx == self.player.y:
                    char_to_draw = self.PLAYER_SYMBOL  # No padding
                    color_attribute = curses.color_pair(self.PLAYER_COLOR_PAIR)
                else:
                    tile = self.world_map.get_tile(x_tile_idx, y_tile_idx)
                    if tile:
                        char_to_draw, display_type = tile.get_display_info()
                        if display_type == "monster":
                            color_attribute = curses.color_pair(self.MONSTER_COLOR_PAIR)
                        elif display_type == "item":
                            color_attribute = curses.color_pair(self.ITEM_COLOR_PAIR)
                        elif display_type == "wall":
                            color_attribute = curses.color_pair(self.WALL_COLOR_PAIR)
                        elif display_type == "floor":
                            color_attribute = curses.color_pair(self.FLOOR_COLOR_PAIR)
                        else:
                            color_attribute = curses.color_pair(0)
                    else:
                        char_to_draw = TILE_SYMBOLS["unknown"]
                        color_attribute = curses.color_pair(0)

                try:
                    self.stdscr.addstr(
                        y_map_idx, current_screen_x, char_to_draw, color_attribute
                    )
                except curses.error:
                    break
                current_screen_x += 1

        hp_line_y = max_y_curses_rows
        if hp_line_y < curses.LINES:
            try:
                self.stdscr.addstr(hp_line_y, 0, f"HP: {self.player.health}")
            except curses.error:
                pass
        else:
            hp_line_y = curses.LINES - UI_LINES_BUFFER

        mode_line_y = hp_line_y + 1
        if mode_line_y < curses.LINES:
            try:
                self.stdscr.addstr(mode_line_y, 0, f"MODE: {self.input_mode.upper()}")
            except curses.error:
                pass
        else:
            mode_line_y = (
                curses.LINES - (UI_LINES_BUFFER - 1)
                if UI_LINES_BUFFER > 1
                else curses.LINES - 1
            )

        message_start_y = mode_line_y + 1
        if self.input_mode == "command":
            if message_start_y < curses.LINES:
                try:
                    prompt = f"> {self.current_command_buffer}"
                    self.stdscr.addstr(message_start_y, 0, prompt[: curses.COLS - 1])
                    message_start_y += 1
                except curses.error:
                    pass

        available_lines = curses.LINES - message_start_y
        num_to_display = min(len(self.message_log), max(0, available_lines))
        start_idx = max(0, len(self.message_log) - num_to_display)

        for i, message in enumerate(self.message_log[start_idx:]):
            current_message_y = message_start_y + i
            if current_message_y < curses.LINES:
                truncated_msg = message[: curses.COLS - 1]
                try:
                    self.stdscr.addstr(current_message_y, 0, truncated_msg)
                except curses.error:
                    break
            else:
                break

        if not self.debug_mode:
            self.stdscr.refresh()

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
                    msg = f"You bump into a {target_tile.monster.name}!"
                    self.message_log.append(msg)
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
            can_take = (
                tile
                and tile.item
                and (argument is None or tile.item.name.lower() == argument.lower())
            )
            if can_take:
                item_taken = self.world_map.remove_item(self.player.x, self.player.y)
                if item_taken:
                    self.player.take_item(item_taken)
                    self.message_log.append(f"You take the {item_taken.name}.")
                    is_quest_win = (
                        self.player.x,
                        self.player.y,
                    ) == self.win_pos and item_taken.properties.get("type") == "quest"
                    if is_quest_win:
                        self.message_log.append(
                            "You picked up the Amulet of Yendor! You win!"
                        )
                        self.game_over = True
                else:
                    self.message_log.append("Error: Tried to take item but failed.")
            else:
                no_item_msg = (
                    f"There is no {argument} here to take."
                    if argument
                    else "Nothing here to take or item name mismatch."
                )
                self.message_log.append(no_item_msg)

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
                    msg = f"You can't drop {dropped_item.name} here, space occupied."
                    self.message_log.append(msg)
            else:
                self.message_log.append(f"You don't have a {argument} to drop.")

        elif verb == "use":
            if argument is None:
                self.message_log.append("What do you want to use?")
                return
            message = self.player.use_item(argument)
            self.message_log.append(message)

        elif verb == "attack":
            adj_monsters_coords = self._get_adjacent_monsters(
                self.player.x, self.player.y
            )
            target_monster, target_x, target_y = None, -1, -1
            if argument:
                named_targets = [
                    (m, mx, my)
                    for m, mx, my in adj_monsters_coords
                    if m.name.lower() == argument.lower()
                ]
                if len(named_targets) == 1:
                    target_monster, target_x, target_y = named_targets[0]
                elif len(named_targets) > 1:
                    self.message_log.append(f"Multiple {argument}s found. Which one?")
                else:
                    msg = f"There is no monster named {argument} nearby."
                    self.message_log.append(msg)
            else:
                if not adj_monsters_coords:
                    self.message_log.append("There is no monster nearby to attack.")
                elif len(adj_monsters_coords) == 1:
                    target_monster, target_x, target_y = adj_monsters_coords[0]
                else:
                    names = ", ".join(
                        sorted(list(set(m.name for m, _, _ in adj_monsters_coords)))
                    )
                    self.message_log.append(
                        f"Multiple monsters nearby: {names}. Which one?"
                    )

            if target_monster and target_x != -1 and target_y != -1:
                dmg_dealt = self.player.attack_monster(target_monster)
                self.message_log.append(
                    f"You attack the {target_monster.name} for {dmg_dealt} damage."
                )
                if target_monster.health <= 0:
                    self.world_map.remove_monster(target_x, target_y)
                    self.message_log.append(f"You defeated the {target_monster.name}!")
                else:
                    dmg_taken = target_monster.attack(self.player)
                    msg = (
                        f"The {target_monster.name} attacks you for {dmg_taken} damage."
                    )
                    self.message_log.append(msg)
                    if self.player.health <= 0:
                        self.message_log.append("You have been defeated. Game Over.")
                        self.game_over = True

        elif verb == "inventory":
            if self.player.inventory:
                item_names = ", ".join([item.name for item in self.player.inventory])
                self.message_log.append(f"Inventory: {item_names}")
            else:
                self.message_log.append("Your inventory is empty.")

        elif verb == "look":
            tile = self.world_map.get_tile(self.player.x, self.player.y)
            self.message_log.append(f"You are at ({self.player.x}, {self.player.y}).")
            if tile:
                if tile.item:
                    self.message_log.append(f"You see a {tile.item.name} here.")
                if tile.monster:
                    self.message_log.append(f"There is a {tile.monster.name} here!")

                adj_monsters = self._get_adjacent_monsters(self.player.x, self.player.y)
                if adj_monsters:
                    for m, x_coord, y_coord in adj_monsters:
                        self.message_log.append(
                            f"You see a {m.name} at ({x_coord}, {y_coord})."
                        )
                elif not tile.item and not tile.monster and not adj_monsters:
                    self.message_log.append("The area is clear.")

        elif verb == "quit":
            self.message_log.append("Quitting game.")
            self.game_over = True

    def _get_adjacent_monsters(
        self, x: int, y: int
    ) -> list[tuple["Monster", int, int]]:  # noqa: F821
        adjacent_monsters = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            adj_x, adj_y = x + dx, y + dy
            tile = self.world_map.get_tile(adj_x, adj_y)
            if tile and tile.monster:
                adjacent_monsters.append((tile.monster, adj_x, adj_y))
        return adjacent_monsters

    def run(self):
        if self.debug_mode:
            print(
                "Error: GameEngine.run() called in debug_mode. "
                "Use main_debug() in main.py for testing."
            )
            return
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
            if not self.debug_mode and hasattr(self, "stdscr") and self.stdscr:
                self.stdscr.keypad(False)
                curses.echo()
                curses.nocbreak()
                curses.endwin()

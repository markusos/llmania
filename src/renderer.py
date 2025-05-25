import curses

from src.tile import TILE_SYMBOLS


class Renderer:
    def __init__(self, stdscr, map_width: int, map_height: int, player_symbol: str):
        self.stdscr = stdscr
        self.map_width = map_width
        self.map_height = map_height
        self.player_symbol = player_symbol

        if (
            self.stdscr
        ):  # Only initialize curses if stdscr is provided (not in debug_mode)
            curses.start_color()
            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(True)
            curses.curs_set(0)  # Default to hidden cursor

            # Initialize color pairs
            # TODO: Define specific colors for these pairs later
            curses.init_pair(
                1, curses.COLOR_BLACK, curses.COLOR_GREEN
            )  # Example: Floor
            self.FLOOR_COLOR_PAIR = 1
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Example: Wall
            self.WALL_COLOR_PAIR = 2
            curses.init_pair(
                3, curses.COLOR_BLACK, curses.COLOR_GREEN
            )  # Example: Player
            self.PLAYER_COLOR_PAIR = 3
            curses.init_pair(
                4, curses.COLOR_BLACK, curses.COLOR_GREEN
            )  # Example: Monster
            self.MONSTER_COLOR_PAIR = 4
            curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Example: Item
            self.ITEM_COLOR_PAIR = 5
            # Add more color pairs (e.g., specific items, monsters, UI text)
            curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default text
            self.DEFAULT_TEXT_COLOR_PAIR = 6
        else:  # In debug_mode, stdscr is None, provide default values for color pairs
            self.FLOOR_COLOR_PAIR = 0
            self.WALL_COLOR_PAIR = 0
            self.PLAYER_COLOR_PAIR = 0
            self.MONSTER_COLOR_PAIR = 0
            self.ITEM_COLOR_PAIR = 0
            self.DEFAULT_TEXT_COLOR_PAIR = 0

    def render_all(
        self,
        player_x: int,
        player_y: int,
        player_health: int,
        world_map,  # world_map: WorldMap
        input_mode: str,
        current_command_buffer: str,
        message_log: list[str],
        debug_render_to_list: bool = False,
    ):
        if debug_render_to_list:
            output_buffer = []
            # For debug rendering, use full map height and width from world_map
            max_y_map = world_map.height
            max_x_map = world_map.width

            for y_map in range(max_y_map):
                row_str = ""
                for x_map in range(max_x_map):
                    char_to_draw = ""
                    if x_map == player_x and y_map == player_y:
                        char_to_draw = self.player_symbol
                    else:
                        tile = world_map.get_tile(x_map, y_map)
                        if tile:
                            symbol, _ = tile.get_display_info()
                            char_to_draw = symbol
                        else:
                            char_to_draw = TILE_SYMBOLS["unknown"]
                    row_str += char_to_draw
                output_buffer.append(row_str)

            # UI elements
            output_buffer.append(f"HP: {player_health}")
            output_buffer.append(f"MODE: {input_mode.upper()}")
            if input_mode == "command":
                output_buffer.append(f"> {current_command_buffer}")
            for message in message_log:
                output_buffer.append(message)
            return output_buffer

        # Main rendering path using curses
        if (
            not self.stdscr
        ):  # Should not happen if not debug_render_to_list and stdscr is None
            # This case implies debug_mode is True but debug_render_to_list is False,
            # which is an invalid state for curses rendering.
            # Or, stdscr was not initialized properly.
            # print(
            #   "Error: Curses rendering called when stdscr is not available "
            #   "and not in debug_render_to_list mode."
            # )
            return

        self.stdscr.clear()
        UI_LINES_BUFFER = 4  # Number of lines for UI

        # Ensure curses.LINES and curses.COLS are valid
        try:
            curses_lines = curses.LINES
            curses_cols = curses.COLS
        except curses.error:  # More specific exception for curses issues
            curses_lines = 24  # common default
            curses_cols = 80  # common default

        max_y_curses_rows = min(self.map_height, curses_lines - UI_LINES_BUFFER)
        max_x_curses_cols = curses_cols - 1  # Leave one col for border/cursor issues

        for y_map_idx in range(max_y_curses_rows):
            current_screen_x = 0
            for x_tile_idx in range(self.map_width):  # Use self.map_width
                if current_screen_x >= max_x_curses_cols:
                    break

                char_to_draw = ""
                color_attribute = curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR)

                if x_tile_idx == player_x and y_map_idx == player_y:
                    char_to_draw = self.player_symbol
                    color_attribute = curses.color_pair(self.PLAYER_COLOR_PAIR)
                else:
                    tile = world_map.get_tile(x_tile_idx, y_map_idx)
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
                        # else default color_attribute
                    else:
                        char_to_draw = TILE_SYMBOLS["unknown"]
                        # default color_attribute

                try:
                    self.stdscr.addstr(
                        y_map_idx, current_screen_x, char_to_draw, color_attribute
                    )
                except curses.error:  # Stop if drawing fails (e.g. window too small)
                    break
                current_screen_x += 1

        # UI Rendering
        hp_line_y = max_y_curses_rows
        if hp_line_y < curses_lines:
            try:
                self.stdscr.addstr(
                    hp_line_y,
                    0,
                    f"HP: {player_health}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
            except curses.error:
                pass  # Avoid crash if cannot draw
        else:  # Should not happen if UI_LINES_BUFFER is respected
            hp_line_y = curses_lines - UI_LINES_BUFFER

        mode_line_y = hp_line_y + 1
        if mode_line_y < curses_lines:
            try:
                self.stdscr.addstr(
                    mode_line_y,
                    0,
                    f"MODE: {input_mode.upper()}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
            except curses.error:
                pass
        else:
            mode_line_y = (
                curses_lines - (UI_LINES_BUFFER - 1)
                if UI_LINES_BUFFER > 1
                else curses_lines - 1
            )

        message_start_y = mode_line_y + 1
        if input_mode == "command":
            if message_start_y < curses_lines:
                try:
                    prompt = f"> {current_command_buffer}"
                    self.stdscr.addstr(
                        message_start_y,
                        0,
                        prompt[: curses_cols - 1],
                        curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                    )
                    message_start_y += (
                        1  # Move message log down if command buffer is shown
                    )
                except curses.error:
                    pass

        # Message Log
        available_lines_for_log = curses_lines - message_start_y
        num_messages_to_display = min(len(message_log), max(0, available_lines_for_log))
        start_message_idx = max(0, len(message_log) - num_messages_to_display)

        for i, message in enumerate(message_log[start_message_idx:]):
            current_message_y = message_start_y + i
            if current_message_y < curses_lines:
                truncated_msg = message[: curses_cols - 1]
                try:
                    self.stdscr.addstr(
                        current_message_y,
                        0,
                        truncated_msg,
                        curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                    )
                except curses.error:  # Stop if drawing fails
                    break
            else:  # No more lines available
                break

        if self.stdscr:
            self.stdscr.refresh()

    def cleanup_curses(self):
        if self.stdscr:  # Only run if stdscr was initialized
            self.stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

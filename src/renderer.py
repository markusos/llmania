import curses  # Changed from shutil to curses for terminal size
from typing import List, Optional, Tuple

from src.message_log import MessageLog
from src.tile import TILE_SYMBOLS
from src.world_map import WorldMap


class Renderer:
    def __init__(
        self, debug_mode: bool, map_width: int, map_height: int, player_symbol: str
    ):
        self.debug_mode = debug_mode
        self.map_width = map_width
        self.map_height = map_height
        self.player_symbol = player_symbol
        self.stdscr = None

        if self.debug_mode:
            self.FLOOR_COLOR_PAIR = 0
            self.WALL_COLOR_PAIR = 0
            self.PLAYER_COLOR_PAIR = 0
            self.MONSTER_COLOR_PAIR = 0
            self.ITEM_COLOR_PAIR = 0
            self.DEFAULT_TEXT_COLOR_PAIR = 0
            self.PATH_COLOR_PAIR = 0
        else:
            self.stdscr = curses.initscr()
            curses.start_color()
            curses.noecho()
            curses.cbreak()
            if self.stdscr:
                self.stdscr.keypad(True)
            curses.curs_set(0)
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.FLOOR_COLOR_PAIR = 1
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            self.WALL_COLOR_PAIR = 2
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.PLAYER_COLOR_PAIR = 3
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_GREEN)
            self.MONSTER_COLOR_PAIR = 4
            curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_GREEN)
            self.ITEM_COLOR_PAIR = 5
            curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
            self.DEFAULT_TEXT_COLOR_PAIR = 6
            curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_GREEN)
            self.PATH_COLOR_PAIR = 7

    def render_all(
        self,
        player_x: int,
        player_y: int,
        player_health: int,
        world_map_to_render: WorldMap,
        input_mode: str,
        current_command_buffer: str,
        message_log: MessageLog,
        current_floor_id: int,
        debug_render_to_list: bool = False,
        ai_path: Optional[List[Tuple[int, int, int]]] = None,
    ) -> list[str] | None:
        if not debug_render_to_list and not self.stdscr and not self.debug_mode:
            print("Error: Renderer.stdscr not initialized for curses rendering.")
            return None

        if debug_render_to_list or self.debug_mode:
            output_buffer = []
            for y_map in range(world_map_to_render.height):
                row_str = ""
                for x_map in range(world_map_to_render.width):
                    char_to_draw = ""
                    # is_path_tile = False # Not used in debug list rendering directly
                    if x_map == player_x and y_map == player_y:
                        char_to_draw = self.player_symbol
                    elif ai_path:
                        path_segment_on_current_floor = [
                            (px, py)
                            for px, py, pf_id in ai_path
                            if pf_id == current_floor_id
                        ]
                        current_coord_xy = (x_map, y_map)
                        if path_segment_on_current_floor:
                            if (
                                current_coord_xy == (ai_path[-1][0], ai_path[-1][1])
                                and current_floor_id == ai_path[-1][2]
                            ):
                                char_to_draw = "x"
                                # is_path_tile = True # Not used for list output
                            elif current_coord_xy in path_segment_on_current_floor:
                                char_to_draw = "*"
                                # is_path_tile = True # Not used for list output

                    if not char_to_draw:
                        tile = world_map_to_render.get_tile(x_map, y_map)
                        if tile:
                            # In debug/list mode, fog is implicitly handled by
                            # tile.get_display_info if visible_map is passed
                            symbol, _ = tile.get_display_info(apply_fog=True)
                            char_to_draw = symbol
                        else:  # Should not happen if map is complete
                            char_to_draw = TILE_SYMBOLS.get("fog", " ")
                    row_str += char_to_draw
                output_buffer.append(row_str)

            output_buffer.append(f"HP: {player_health}")
            output_buffer.append(f"Floor: {current_floor_id}")
            output_buffer.append(f"MODE: {input_mode.upper()}")
            if input_mode == "command":
                output_buffer.append(f"> {current_command_buffer}")

            messages_for_debug = message_log.get_messages()  # Use MessageLog method
            for msg_debug in messages_for_debug:  # Iterate directly
                output_buffer.append(msg_debug)
            return output_buffer

        # Curses rendering path (remains largely the same)
        if not self.stdscr:
            print("Critical Error: stdscr is None during curses rendering attempt.")
            return None
        self.stdscr.clear()
        UI_LINES_BUFFER = 5
        try:
            curses_lines = curses.LINES
            curses_cols = curses.COLS
        except curses.error:
            curses_lines, curses_cols = 24, 80

        max_y_curses_rows = min(self.map_height, curses_lines - UI_LINES_BUFFER)
        max_x_curses_cols = curses_cols - 1

        for y_map_idx in range(max_y_curses_rows):
            current_screen_x = 0
            for x_tile_idx in range(self.map_width):
                if current_screen_x >= max_x_curses_cols:
                    break
                char_to_draw = ""
                color_attribute = curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR)

                if x_tile_idx == player_x and y_map_idx == player_y:
                    char_to_draw = self.player_symbol
                    color_attribute = curses.color_pair(self.PLAYER_COLOR_PAIR)
                elif ai_path:
                    path_segment = [
                        (px, py) for px, py, fid in ai_path if fid == current_floor_id
                    ]
                    current_xy = (x_tile_idx, y_map_idx)
                    if current_xy in path_segment:
                        # If current_xy is the last point of ai_path on current floor
                        if (
                            current_xy == (ai_path[-1][0], ai_path[-1][1])
                            and current_floor_id == ai_path[-1][2]
                        ):
                            char_to_draw = "x"
                        else:
                            char_to_draw = "*"
                        color_attribute = curses.color_pair(self.PATH_COLOR_PAIR)

                if not char_to_draw:  # If not player or path tile already set
                    tile = world_map_to_render.get_tile(x_tile_idx, y_map_idx)
                    if tile:
                        # Fog is handled by get_display_info based on tile.is_explored
                        char_to_draw, display_type = tile.get_display_info(
                            apply_fog=True
                        )
                        if display_type == "monster":
                            color_attribute = curses.color_pair(self.MONSTER_COLOR_PAIR)
                        elif display_type == "item":
                            color_attribute = curses.color_pair(self.ITEM_COLOR_PAIR)
                        elif display_type == "wall":
                            color_attribute = curses.color_pair(self.WALL_COLOR_PAIR)
                        elif display_type == "floor":
                            color_attribute = curses.color_pair(self.FLOOR_COLOR_PAIR)
                        elif display_type == "fog":
                            color_attribute = curses.color_pair(
                                self.DEFAULT_TEXT_COLOR_PAIR
                            )
                            if char_to_draw == " ":
                                color_attribute = curses.color_pair(
                                    0
                                )  # Use default bg for space fog
                        # else default color pair
                    else:  # Should not happen
                        char_to_draw = TILE_SYMBOLS.get("fog", " ")
                        color_attribute = (
                            curses.color_pair(0)
                            if char_to_draw == " "
                            else curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR)
                        )

                try:
                    self.stdscr.addstr(
                        y_map_idx, current_screen_x, char_to_draw, color_attribute
                    )
                except curses.error:
                    break
                current_screen_x += 1

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
                pass

        floor_line_y = hp_line_y + 1
        if floor_line_y < curses_lines:
            try:
                self.stdscr.addstr(
                    floor_line_y,
                    0,
                    f"Floor: {current_floor_id}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
            except curses.error:
                pass

        mode_line_y = floor_line_y + 1
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
                    message_start_y += 1
                except curses.error:
                    pass

        available_lines_for_log = curses_lines - message_start_y
        if available_lines_for_log > 0:
            messages = message_log.get_messages()
            num_to_display = min(len(messages), available_lines_for_log)
            start_idx = max(0, len(messages) - num_to_display)

            rendered_count = 0
            for i, msg_text in enumerate(messages[start_idx:]):
                msg_y = message_start_y + i
                if msg_y < curses_lines:
                    try:
                        self.stdscr.move(msg_y, 0)
                        self.stdscr.clrtoeol()
                        self.stdscr.addstr(
                            msg_y,
                            0,
                            msg_text[: curses_cols - 1],
                            curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                        )
                        rendered_count += 1
                    except curses.error:
                        break
                else:
                    break

            # Clear lines not used by current messages but part of log area
            # This uses message_log.max_messages to know how many lines log *could* take
            for i in range(rendered_count, message_log.max_messages):
                msg_y = message_start_y + i
                if msg_y < curses_lines:
                    try:
                        self.stdscr.move(msg_y, 0)
                        self.stdscr.clrtoeol()
                    except curses.error:
                        break
                else:
                    break

        self.stdscr.refresh()
        return None

    def cleanup_curses(self):
        if self.stdscr and not self.debug_mode:
            self.stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

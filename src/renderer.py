import curses  # Changed from shutil to curses for terminal size
from typing import TYPE_CHECKING, List, Optional, Tuple

from src.input_mode import InputMode
from src.message_log import MessageLog
from src.tile import TILE_SYMBOLS
from src.world_map import WorldMap

if TYPE_CHECKING:
    from src.player import Player


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
            self.FLOOR_DIM_COLOR_PAIR = 0
            self.WALL_DIM_COLOR_PAIR = 0
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
            # Dim colors for explored but not currently visible tiles
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_CYAN)
            self.FLOOR_DIM_COLOR_PAIR = 8
            curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK)
            self.WALL_DIM_COLOR_PAIR = 9

    def render_all(
        self,
        player_x: int,
        player_y: int,
        player_health: int,
        world_map_to_render: WorldMap,
        input_mode: InputMode,
        current_command_buffer: str,
        message_log: MessageLog,
        current_floor_id: int,
        debug_render_to_list: bool = False,
        ai_path: Optional[List[Tuple[int, int, int]]] = None,
        apply_fog: bool = True,
        ai_state: Optional[str] = None,
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
                            symbol, _ = tile.get_display_info(apply_fog=apply_fog)
                            char_to_draw = symbol
                        else:  # Should not happen if map is complete
                            char_to_draw = TILE_SYMBOLS.get("fog", " ")
                    row_str += char_to_draw
                output_buffer.append(row_str)

            output_buffer.append(f"HP: {player_health}")
            output_buffer.append(f"Floor: {current_floor_id}")
            output_buffer.append(f"MODE: {input_mode.name.upper()}")
            if ai_state:
                output_buffer.append(f"AI State: {ai_state}")
                output_buffer.append(f"Position: ({player_x}, {player_y})")
            if input_mode == InputMode.COMMAND:
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
        UI_LINES_BUFFER = 7 if ai_state else 5
        try:
            curses_lines = curses.LINES
            curses_cols = curses.COLS
        except curses.error:
            curses_lines, curses_cols = 24, 80

        # Calculate viewport dimensions (how many tiles we can display)
        viewport_height = min(self.map_height, curses_lines - UI_LINES_BUFFER)
        viewport_width = min(self.map_width, curses_cols - 1)

        # Calculate viewport offset to center on player
        # If the map is smaller than the viewport, offset is 0
        # Otherwise, center the viewport on the player, clamping to map bounds
        if self.map_height <= viewport_height:
            viewport_y_offset = 0
        else:
            # Center vertically on player
            viewport_y_offset = player_y - viewport_height // 2
            # Clamp to valid range [0, map_height - viewport_height]
            viewport_y_offset = max(
                0, min(viewport_y_offset, self.map_height - viewport_height)
            )

        if self.map_width <= viewport_width:
            viewport_x_offset = 0
        else:
            # Center horizontally on player
            viewport_x_offset = player_x - viewport_width // 2
            # Clamp to valid range [0, map_width - viewport_width]
            viewport_x_offset = max(
                0, min(viewport_x_offset, self.map_width - viewport_width)
            )

        for screen_y in range(viewport_height):
            current_screen_x = 0
            map_y = screen_y + viewport_y_offset
            for screen_x in range(viewport_width):
                if current_screen_x >= viewport_width:
                    break
                map_x = screen_x + viewport_x_offset
                char_to_draw = ""
                color_attribute = curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR)

                if map_x == player_x and map_y == player_y:
                    char_to_draw = self.player_symbol
                    color_attribute = curses.color_pair(self.PLAYER_COLOR_PAIR)
                elif ai_path:
                    path_segment = [
                        (px, py) for px, py, fid in ai_path if fid == current_floor_id
                    ]
                    current_xy = (map_x, map_y)
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
                    tile = world_map_to_render.get_tile(map_x, map_y)
                    if tile:
                        # Fog is handled by get_display_info based on tile.is_explored
                        # show_visibility enables dim rendering for explored-not-visible
                        char_to_draw, display_type = tile.get_display_info(
                            apply_fog=True, show_visibility=True
                        )
                        if display_type == "monster":
                            color_attribute = curses.color_pair(self.MONSTER_COLOR_PAIR)
                        elif display_type == "item":
                            color_attribute = curses.color_pair(self.ITEM_COLOR_PAIR)
                        elif display_type == "wall":
                            color_attribute = curses.color_pair(self.WALL_COLOR_PAIR)
                        elif display_type == "wall_dim":
                            color_attribute = curses.color_pair(
                                self.WALL_DIM_COLOR_PAIR
                            )
                        elif display_type == "floor":
                            color_attribute = curses.color_pair(self.FLOOR_COLOR_PAIR)
                        elif display_type == "floor_dim":
                            color_attribute = curses.color_pair(
                                self.FLOOR_DIM_COLOR_PAIR
                            )
                        elif display_type == "portal_dim":
                            color_attribute = curses.color_pair(
                                self.FLOOR_DIM_COLOR_PAIR
                            )
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
                        screen_y, current_screen_x, char_to_draw, color_attribute
                    )
                except curses.error:
                    break
                current_screen_x += 1

        next_line_y = viewport_height
        if next_line_y < curses_lines:
            try:
                self.stdscr.addstr(
                    next_line_y,
                    0,
                    f"HP: {player_health}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
                next_line_y += 1
            except curses.error:
                pass

        if next_line_y < curses_lines:
            try:
                self.stdscr.addstr(
                    next_line_y,
                    0,
                    f"Floor: {current_floor_id}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
                next_line_y += 1
            except curses.error:
                pass

        if next_line_y < curses_lines:
            try:
                self.stdscr.addstr(
                    next_line_y,
                    0,
                    f"MODE: {input_mode.name.upper()}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
                next_line_y += 1
            except curses.error:
                pass

        if ai_state:
            if next_line_y < curses_lines:
                try:
                    self.stdscr.addstr(
                        next_line_y,
                        0,
                        f"AI State: {ai_state}",
                        curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                    )
                    next_line_y += 1
                except curses.error:
                    pass
            if next_line_y < curses_lines:
                try:
                    self.stdscr.addstr(
                        next_line_y,
                        0,
                        f"Position: ({player_x}, {player_y})",
                        curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                    )
                    next_line_y += 1
                except curses.error:
                    pass

        message_start_y = next_line_y
        if input_mode == InputMode.COMMAND:
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

    def render_inventory(self, player: "Player") -> Optional[List[str]]:
        if self.debug_mode:
            output_buffer = ["--- Inventory ---"]
            output_buffer.append(f"Health: {player.health}/{player.get_max_health()}")
            output_buffer.append(f"Attack: {player.get_attack_power()}")
            output_buffer.append(f"Defense: {player.get_defense()}")
            output_buffer.append(f"Speed: {player.get_speed()}")
            output_buffer.append("\n--- Equipment ---")
            for slot, item in player.equipment.slots.items():
                item_name = item.name if item else "Empty"
                output_buffer.append(f"{slot.capitalize()}: {item_name}")
            output_buffer.append("\n--- Items ---")
            if not player.inventory.items:
                output_buffer.append("Your inventory is empty.")
            else:
                for item in player.inventory.items:
                    output_buffer.append(f"- {item.name}")
            return output_buffer

        if not self.stdscr:
            return None

        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Title
        self.stdscr.addstr(1, 2, "--- Inventory ---", curses.A_BOLD)

        # Stats
        self.stdscr.addstr(3, 2, "Stats", curses.A_UNDERLINE)
        self.stdscr.addstr(4, 2, f"Health: {player.health}/{player.get_max_health()}")
        self.stdscr.addstr(5, 2, f"Attack: {player.get_attack_power()}")
        self.stdscr.addstr(6, 2, f"Defense: {player.get_defense()}")
        self.stdscr.addstr(7, 2, f"Speed: {player.get_speed()}")

        # Equipment
        if 9 < height - 1:
            self.stdscr.addstr(9, 2, "Equipment", curses.A_UNDERLINE)
        row = 10
        for slot, item in player.equipment.slots.items():
            if row >= height - 1:
                break
            item_name = item.name if item else "Empty"
            self.stdscr.addstr(row, 2, f"{slot.capitalize()}: {item_name}")
            row += 1

        # Inventory
        if row + 1 < height - 1:
            self.stdscr.addstr(row + 1, 2, "Items", curses.A_UNDERLINE)
        row += 2
        if not player.inventory.items:
            if row < height - 1:
                self.stdscr.addstr(row, 2, "Your inventory is empty.")
        else:
            for item in player.inventory.items:
                if row >= height - 1:
                    break
                self.stdscr.addstr(row, 2, f"- {item.name}")
                row += 1

        self.stdscr.refresh()
        return None

    def cleanup_curses(self):
        if self.stdscr and not self.debug_mode:
            self.stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

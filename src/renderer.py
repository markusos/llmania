import curses
from typing import List, Optional, Tuple  # Added Optional, List, Tuple

from src.message_log import MessageLog
from src.tile import TILE_SYMBOLS
from src.world_map import WorldMap  # Added for type hinting


class Renderer:
    """
    Handles all rendering aspects of the game, including the map, UI elements,
    and messages. It can operate in a curses-based terminal mode or a
    debug mode that outputs to a list of strings.
    """

    def __init__(
        self, debug_mode: bool, map_width: int, map_height: int, player_symbol: str
    ):
        """
        Initializes the Renderer.

        Args:
            debug_mode: If True, curses is not initialized, and rendering targets
                        a list of strings. If False, curses is initialized for
                        terminal display.
            map_width: The width of the game map to be rendered.
            map_height: The height of the game map to be rendered.
            player_symbol: The character symbol used to represent the player.
        """
        self.debug_mode = debug_mode
        self.map_width = map_width
        self.map_height = map_height
        self.player_symbol = player_symbol
        self.stdscr = (
            None  # Will be set to the curses screen object if not in debug_mode
        )

        if self.debug_mode:
            # In debug_mode, stdscr is None. Color pairs not used for list rendering.
            # Define placeholder values for color pairs for attribute existence.
            self.FLOOR_COLOR_PAIR = 0
            self.WALL_COLOR_PAIR = 0
            self.PLAYER_COLOR_PAIR = 0
            self.MONSTER_COLOR_PAIR = 0
            self.ITEM_COLOR_PAIR = 0
            self.DEFAULT_TEXT_COLOR_PAIR = 0
            self.PATH_COLOR_PAIR = 0  # Placeholder for debug mode
        else:
            # Initialize curses for terminal-based rendering.
            self.stdscr = curses.initscr()  # Initialize the curses library.
            curses.start_color()  # Enable color support.
            curses.noecho()  # Turn off automatic echoing of keys to the screen.
            curses.cbreak()  # React to keys instantly, without requiring Enter.
            if self.stdscr:
                self.stdscr.keypad(True)  # Enable special keys (like arrow keys).
            curses.curs_set(0)  # Make the cursor invisible by default.

            # Define color pairs used for different game elements.
            # Format: curses.init_pair(pair_number, foreground_color, background_color)
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Floor
            self.FLOOR_COLOR_PAIR = 1
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Wall
            self.WALL_COLOR_PAIR = 2
            curses.init_pair(
                3, curses.COLOR_BLACK, curses.COLOR_GREEN
            )  # Player (Same as floor for now)
            self.PLAYER_COLOR_PAIR = 3
            curses.init_pair(
                4, curses.COLOR_RED, curses.COLOR_GREEN
            )  # Monster (Distinct color)
            self.MONSTER_COLOR_PAIR = 4
            curses.init_pair(
                5, curses.COLOR_YELLOW, curses.COLOR_GREEN
            )  # Item (Distinct color)
            self.ITEM_COLOR_PAIR = 5
            curses.init_pair(
                6, curses.COLOR_WHITE, curses.COLOR_BLACK
            )  # Default text (e.g., for UI)
            self.DEFAULT_TEXT_COLOR_PAIR = 6
            curses.init_pair(7, curses.COLOR_BLUE, curses.COLOR_GREEN)  # Path
            self.PATH_COLOR_PAIR = 7

    def render_all(
        self,
        player_x: int,
        player_y: int,
        player_health: int,
        world_map_to_render: WorldMap,  # This will be the main map or AI's visible map
        input_mode: str,
        current_command_buffer: str,
        message_log: MessageLog,
        current_floor_id: int,  # Added to display current floor
        debug_render_to_list: bool = False,
        ai_path: Optional[List[Tuple[int, int, int]]] = None,  # Path includes floor_id
        # ai_mode_active: bool = False,  # Parameter removed, fog is always
        # active based on visible_map
    ) -> list[str] | None:
        """
        Renders the entire game screen, including map, player, entities, UI,
        and messages using the provided `world_map_to_render` (which is expected
        to be the `visible_map` from GameEngine, incorporating fog of war).

        If `debug_render_to_list` is True, output is a list of strings representing
        the screen content. Otherwise, renders to the curses terminal.
        Fog of war is applied based on the `is_explored` attribute of tiles in
        `world_map_to_render`.

        Args:
            player_x: Player's current x-coordinate.
            player_y: Player's current y-coordinate.
            player_health: Player's current health.
            world_map_to_render: The WorldMap object to display (expected to be
                the `visible_map`).
            input_mode: The current input mode ("movement" or "command").
            current_command_buffer: The text currently in the command input buffer.
            message_log: A list of messages to display to the player.
            debug_render_to_list: If True, renders to a list of strings
                instead of curses.

        Returns:
            A list of strings if `debug_render_to_list` is True, otherwise None.
        """
        if not debug_render_to_list and not self.stdscr and not self.debug_mode:
            print("Error: Renderer.stdscr not initialized for curses rendering.")
            return None

        # Determine which map to use for dimensions and tile data
        # map_to_use_for_rendering = ai_visible_map if ai_mode_active and
        # ai_visible_map else world_map
        # The caller (GameEngine) will now pass the correct map as world_map_to_render.

        if debug_render_to_list or self.debug_mode:
            output_buffer = []
            for y_map in range(world_map_to_render.height):
                row_str = ""
                for x_map in range(world_map_to_render.width):
                    char_to_draw = ""
                    is_path_tile = False
                    if x_map == player_x and y_map == player_y:
                        char_to_draw = self.player_symbol
                    elif ai_path:
                        # AI path is List[Tuple[int, int, int]]
                        # We only care about path segments on the current_floor_id
                        # for 2D map display.
                        # Check if (x_map, y_map) is part of the path on the current floor
                        path_segment_on_current_floor = [
                            (px, py)
                            for px, py, pf_id in ai_path
                            if pf_id == current_floor_id
                        ]
                        current_coord_xy = (x_map, y_map)

                        if path_segment_on_current_floor:
                            # Check if it's the destination of the segment on this floor
                            # Note: ai_path[-1] is the overall destination (x,y,floor).
                            # We need to check if (x_map,y_map) is the last step
                            # of the path *on this specific floor*.
                            # This logic might need refinement if path can zigzag floors
                            # and then end on current. For now, simple check.
                            if (
                                current_coord_xy == (ai_path[-1][0], ai_path[-1][1])
                                and current_floor_id == ai_path[-1][2]
                            ):
                                char_to_draw = "x"  # Overall destination on this floor
                                is_path_tile = True
                            elif current_coord_xy in path_segment_on_current_floor:
                                char_to_draw = "*"  # Part of path on this floor
                                is_path_tile = True
                            # If the final destination is on another floor, "x" won't show here.
                            # A portal tile leading to it might be marked as '*'.

                    if not char_to_draw:  # If not player or path, draw tile content
                        tile = world_map_to_render.get_tile(x_map, y_map)
                        if tile:
                            symbol, _ = tile.get_display_info(apply_fog=True)
                            char_to_draw = symbol
                        else:
                            char_to_draw = TILE_SYMBOLS.get("fog", " ")
                    row_str += char_to_draw
                output_buffer.append(row_str)

            # Append UI elements as strings to the buffer.
            output_buffer.append(f"HP: {player_health}")
            output_buffer.append(f"Floor: {current_floor_id}")  # Display current floor
            output_buffer.append(f"MODE: {input_mode.upper()}")
            if input_mode == "command":
                output_buffer.append(f"> {current_command_buffer}")

            # Debug mode: Get messages from MessageLog object
            messages_for_debug = message_log.get_messages()
            if messages_for_debug:
                for msg_debug in messages_for_debug:
                    output_buffer.append(msg_debug)
            else:
                # Optional: indicate no messages, or just leave blank
                # output_buffer.append("No messages.")
                pass
            return output_buffer

        # --- Curses-based rendering path ---
        # This part executes only if not (debug_render_to_list or self.debug_mode),
        # which means self.stdscr should be valid.
        if not self.stdscr:  # Safeguard if somehow stdscr is None here
            print("Critical Error: stdscr is None during curses rendering attempt.")
            return None

        self.stdscr.clear()  # Clear the screen before drawing new content.

        # Define a buffer for UI lines at the bottom of the screen.
        # This includes lines for HP, Floor, Mode, Command Input, and some messages.
        UI_LINES_BUFFER = 5  # Increased to accommodate Floor ID

        # Get terminal dimensions. Handle curses error if terminal not ready.
        try:
            curses_lines = curses.LINES
            curses_cols = curses.COLS
        except curses.error:
            # Fallback dimensions if curses.LINES/COLS not available (e.g., resize).
            curses_lines = 24  # A common terminal default height.
            curses_cols = 80  # A common terminal default width.

        # Determine the visible portion of the map based on terminal size.
        # Map rendering area: from y=0 up to (terminal height - UI buffer).
        max_y_curses_rows = min(self.map_height, curses_lines - UI_LINES_BUFFER)
        # Map rendering area: from x=0 up to (terminal width - 1 for safety).
        max_x_curses_cols = (
            curses_cols - 1
        )  # Max characters per line, leave one for safety margin

        # Render the map tiles
        for y_map_idx in range(max_y_curses_rows):  # Iterate over visible map rows
            current_screen_x = 0  # Current character column on the screen for this row
            for x_tile_idx in range(
                self.map_width
            ):  # Iterate over map tiles in this row
                if current_screen_x >= max_x_curses_cols:
                    break  # Stop if we exceed screen width for this row

                char_to_draw = ""
                color_attribute = curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR)
                is_path_tile = False

                if x_tile_idx == player_x and y_map_idx == player_y:
                    char_to_draw = self.player_symbol
                    color_attribute = curses.color_pair(self.PLAYER_COLOR_PAIR)
                elif ai_path:  # ai_path is List[Tuple[int, int, int]]
                    path_segment_on_current_floor = [
                        (px, py)
                        for px, py, pf_id in ai_path
                        if pf_id == current_floor_id
                    ]
                    current_coord_xy = (x_tile_idx, y_map_idx)

                    if path_segment_on_current_floor:
                        if (
                            current_coord_xy == (ai_path[-1][0], ai_path[-1][1])
                            and current_floor_id == ai_path[-1][2]
                        ):
                            char_to_draw = "x"  # Overall destination on this floor
                            color_attribute = curses.color_pair(self.PATH_COLOR_PAIR)
                            is_path_tile = True
                        elif current_coord_xy in path_segment_on_current_floor:
                            char_to_draw = "*"  # Part of path on this floor
                            color_attribute = curses.color_pair(self.PATH_COLOR_PAIR)
                            is_path_tile = True
                if (
                    not is_path_tile and not char_to_draw
                ):  # If not player and not path tile
                    tile = world_map_to_render.get_tile(x_tile_idx, y_map_idx)
                    if tile:
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
                                color_attribute = curses.color_pair(0)
                        # else: default color for "unknown"
                    else:
                        char_to_draw = TILE_SYMBOLS.get("fog", " ")
                        color_attribute = (
                            curses.color_pair(0)
                            if char_to_draw == " "
                            else curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR)
                        )

                # Ensure char_to_draw is not empty if a path tile was identified
                # but char_to_draw wasn't set (e.g. player on path, and player
                # symbol logic might change or have an issue). This is a fallback.
                if is_path_tile and not char_to_draw:
                    # This situation implies that the player symbol should have been
                    # drawn, or there's an unexpected state.
                    # If player isn't at (x_tile_idx, y_map_idx), then path char.
                    if not (x_tile_idx == player_x and y_map_idx == player_y):
                        if (x_tile_idx, y_map_idx) == ai_path[-1]:
                            char_to_draw = "x"  # Destination
                        else:
                            char_to_draw = "*"  # Path segment
                        color_attribute = curses.color_pair(self.PATH_COLOR_PAIR)
                    # If player is here, char_to_draw should already be player_symbol.
                    # If it's not, then the initial player check failed, which is
                    # a deeper issue. This fallback doesn't try to fix that,
                    # it just ensures path tiles get *a* path symbol if not player.

                try:
                    # Add the character to the screen at (y_map_idx, current_screen_x)
                    self.stdscr.addstr(
                        y_map_idx, current_screen_x, char_to_draw, color_attribute
                    )
                except curses.error:
                    # Stop drawing row if error occurs (e.g., drawing outside bounds
                    # due to small terminal window size change).
                    break
                current_screen_x += 1

        # --- UI Rendering ---
        # Calculate starting Y position for UI elements, placed after the map.
        # hp_line_y is the first line after the map rendering area.
        hp_line_y = max_y_curses_rows
        if hp_line_y < curses_lines:  # Ensure there's space for HP line
            try:
                self.stdscr.addstr(
                    hp_line_y,
                    0,
                    f"HP: {player_health}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
            except curses.error:
                pass  # Avoid crash if cannot draw (e.g. terminal too small)

        # Floor ID line is one line below HP.
        floor_line_y = hp_line_y + 1
        if floor_line_y < curses_lines:  # Ensure there's space
            try:
                self.stdscr.addstr(
                    floor_line_y,
                    0,
                    f"Floor: {current_floor_id}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
            except curses.error:
                pass

        # Mode line is one line below Floor ID.
        mode_line_y = floor_line_y + 1
        if mode_line_y < curses_lines:  # Ensure there's space for Mode line
            try:
                self.stdscr.addstr(
                    mode_line_y,
                    0,
                    f"MODE: {input_mode.upper()}",
                    curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                )
            except curses.error:
                pass

        # Message log starts below Mode, or below command buffer in command mode.
        message_start_y = mode_line_y + 1
        if input_mode == "command":
            if message_start_y < curses_lines:  # Ensure space for command prompt
                try:
                    prompt = f"> {current_command_buffer}"
                    # Truncate prompt if it's wider than the screen.
                    self.stdscr.addstr(
                        message_start_y,
                        0,
                        prompt[: curses_cols - 1],
                        curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                    )
                    message_start_y += 1  # Next line for messages
                except curses.error:
                    pass

        # Render Message Log
        # Calculate how many lines are available for the message log.
        available_lines_for_log = curses_lines - message_start_y
        if available_lines_for_log > 0:
            messages_to_render = (
                message_log.get_messages()
            )  # Get messages from MessageLog object

            # Display the most recent messages that fit in the available lines.
            num_messages_to_display = min(
                len(messages_to_render), available_lines_for_log
            )  # Use len(messages_to_render)

            # Get the slice of messages to display (most recent ones).
            # If len < num_messages_to_display, this correctly takes all.
            start_message_idx = max(
                0, len(messages_to_render) - num_messages_to_display
            )

            rendered_message_count = 0
            for i, message_text in enumerate(messages_to_render[start_message_idx:]):
                current_message_y = message_start_y + i
                if (
                    current_message_y < curses_lines
                ):  # Check screen bounds for this message
                    truncated_msg = message_text[: curses_cols - 1]
                    try:
                        self.stdscr.move(current_message_y, 0)
                        self.stdscr.clrtoeol()  # Clear the line
                        self.stdscr.addstr(
                            current_message_y,
                            0,
                            truncated_msg,
                            curses.color_pair(self.DEFAULT_TEXT_COLOR_PAIR),
                        )
                        rendered_message_count += 1
                    except curses.error:
                        break
                else:
                    break

            # Clear remaining lines in message area if fewer than max_messages shown.
            # Assumes message_log.max_messages was 5 (GameEngine setup).
            # Clears lines that might have old messages if current log is shorter.
            max_log_display_lines = (
                message_log.max_messages
            )  # Use actual max_messages from the log object
            for i in range(rendered_message_count, max_log_display_lines):
                current_message_y = message_start_y + i
                if current_message_y < curses_lines:  # Check screen bounds
                    self.stdscr.move(current_message_y, 0)
                    self.stdscr.clrtoeol()
                else:
                    break

        self.stdscr.refresh()  # Refresh the physical screen to show changes.
        return None  # Curses rendering doesn't return a list of strings.

    def cleanup_curses(self):
        """
        Restores the terminal to its normal operating mode.
        This should be called before the program exits if curses was used.
        """
        if (
            self.stdscr and not self.debug_mode
        ):  # Only run if stdscr was initialized and not in general debug_mode
            self.stdscr.keypad(False)  # Disable special key processing.
            curses.echo()  # Turn echoing back on.
            curses.nocbreak()  # Restore buffered input mode.
            curses.endwin()  # Restore terminal to original state.
        # If self.stdscr is None (e.g., debug_mode was True or curses init failed),
        # or if general debug_mode is true, no curses cleanup is needed.

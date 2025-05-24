import curses

from src.parser import Parser
from src.player import Player
from src.tile import TILE_SYMBOLS  # Added ENTITY_SYMBOLS
from src.world_generator import WorldGenerator


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
            curses.start_color()  # Initialize color functionality
            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(True)
            curses.curs_set(0)  # Hide cursor initially

            # Define color pairs
            # Pair 1: Floor (Black on Green)
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.FLOOR_COLOR_PAIR = 1
            # Pair 2: Wall (Black on White) - Changed for better visibility
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            self.WALL_COLOR_PAIR = 2
            # Pair 3: Player (Black on Green) - Assuming player emoji is black or dark
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.PLAYER_COLOR_PAIR = 3
            # Pair 4: Monster (Black on Green) - Assuming monster emoji is black or dark
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.MONSTER_COLOR_PAIR = 4
            # Pair 5: Item (Black on Green) - Assuming item emoji is black or dark
            curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.ITEM_COLOR_PAIR = 5
        else:
            self.stdscr = None  # No curses screen in debug mode
            # In debug mode, we won't have color pairs, but let's define the attributes
            # so that code attempting to access them doesn't immediately crash.
            # They won't be used for actual coloring in debug text output.
            self.FLOOR_COLOR_PAIR = 0  # 0 is default pair
            self.WALL_COLOR_PAIR = 0
            self.PLAYER_COLOR_PAIR = 0
            self.MONSTER_COLOR_PAIR = 0
            self.ITEM_COLOR_PAIR = 0

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
            curses.curs_set(0)
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
                curses.curs_set(1)  # Show cursor
            return command_tuple

        elif self.input_mode == "command":
            curses.curs_set(1)
            # Condition for Enter - submit command
            if (
                key == "\n" or key == curses.KEY_ENTER
            ):  # KEY_ENTER is an integer, '\n' is a string
                command_to_parse = self.current_command_buffer
                self.current_command_buffer = ""
                self.input_mode = "movement"
                curses.curs_set(0)
                command_tuple = self.parser.parse_command(command_to_parse)
                return command_tuple  # Return parsed command
            elif key == "KEY_BACKSPACE" or key == "\x08" or key == "\x7f":
                self.current_command_buffer = self.current_command_buffer[:-1]
            # Condition for Escape key - abort command, switch to movement
            elif key == "\x1b":  # Escape key
                self.current_command_buffer = ""
                self.input_mode = "movement"
                curses.curs_set(0)
            # Condition for 'q' or 'Q' - abort command, switch to movement
            elif key == "q" or key == "Q":
                self.current_command_buffer = ""
                self.input_mode = "movement"
                curses.curs_set(0)
            # Condition for KEY_RESIZE
            elif key == "KEY_RESIZE":  # Handle resize event
                self.stdscr.clear()
                # The next render_map call will redraw based on new screen size
            # Condition for printable characters - append to buffer (should be last)
            elif isinstance(key, str) and len(key) == 1 and key.isprintable():
                self.current_command_buffer += key
            # If none of the above, command not yet submitted or unhandled key
            return None

        # Should only be reached if input_mode is not "movement" or "command"
        return None

    def render_map(self, debug_render_to_list=False):
        if debug_render_to_list:
            output_buffer = []
            # Debug rendering for 3x3 grid structure
            FLOOR_SYMBOL = TILE_SYMBOLS["floor"]
            # For debug rendering, use full map height and width in terms of tiles
            map_tile_height = self.world_map.height
            map_tile_width = self.world_map.width

            # Output buffer will store strings, each representing a screen row
            # Since each tile is 3x3, the screen representation is 3 times larger
            screen_buffer_height = map_tile_height * 3
            # Initialize screen_buffer with empty strings for each screen row
            output_buffer = ["" for _ in range(screen_buffer_height)]

            for y_tile_idx in range(map_tile_height):
                for x_tile_idx in range(map_tile_width):
                    current_tile_grid = []
                    # Determine the 3x3 grid for the current tile
                    if x_tile_idx == self.player.x and y_tile_idx == self.player.y:
                        current_tile_grid = [
                            [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                            [FLOOR_SYMBOL, self.PLAYER_SYMBOL, FLOOR_SYMBOL],
                            [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                        ]
                    else:
                        tile = self.world_map.get_tile(x_tile_idx, y_tile_idx)
                        if tile:
                            # get_display_info now returns a 3x3 grid and a display_type
                            grid_data, _ = tile.get_display_info()
                            current_tile_grid = grid_data
                        else:
                            # Default unknown grid
                            unknown_symbol = TILE_SYMBOLS["unknown"]
                            current_tile_grid = [
                                [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                                [FLOOR_SYMBOL, unknown_symbol, FLOOR_SYMBOL],
                                [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                            ]
                    
                    # Populate the output_buffer with characters from the 3x3 grid
                    for y_offset in range(3):
                        y_screen = y_tile_idx * 3 + y_offset
                        for x_offset in range(3):
                            char_to_draw = current_tile_grid[y_offset][x_offset]
                            # Append character to the correct row string in output_buffer
                            # Ensure the row string is long enough, pad with spaces if necessary
                            # This simple concatenation works because we build row by row, tile by tile
                            output_buffer[y_screen] += char_to_draw
            
            # After map, add UI elements
            # Trim empty trailing rows from the map part if any tile column was shorter
            # This is a simplified approach; for perfect alignment, all rows should extend to max_x_tile_cols * 3
            # For now, let's just append.
            final_output_buffer = [row for row in output_buffer if row] # Remove completely empty rows if any logic error

            final_output_buffer.append(f"HP: {self.player.health}")
            final_output_buffer.append(f"MODE: {self.input_mode.upper()}")
            if self.input_mode == "command":
                final_output_buffer.append(f"> {self.current_command_buffer}")
            for message in self.message_log:  # Log all messages for debug
                final_output_buffer.append(message)
            return final_output_buffer

        # Original curses rendering code
        if self.debug_mode:
            print("Error: Curses rendering called in debug mode without debug_render_to_list=True.")
            return

        self.stdscr.clear()
        FLOOR_SYMBOL = TILE_SYMBOLS["floor"]
        UI_LINES_BUFFER = 4 # Number of lines reserved for UI at the bottom

        # Calculate max number of TILE rows and TILE columns that can be displayed
        max_y_tile_rows = min(self.world_map.height, (curses.LINES - UI_LINES_BUFFER) // 3)
        max_x_tile_cols = (curses.COLS - 1) // 3 # -1 because addstr behavior at edge

        for y_tile_idx in range(max_y_tile_rows):
            for x_tile_idx in range(self.world_map.width):
                if x_tile_idx >= max_x_tile_cols:
                    break # No more space in this screen row for more tiles

                current_tile_grid = []
                display_type = "unknown" # Default

                if x_tile_idx == self.player.x and y_tile_idx == self.player.y:
                    display_type = "player"
                    current_tile_grid = [
                        [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                        [FLOOR_SYMBOL, self.PLAYER_SYMBOL, FLOOR_SYMBOL],
                        [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                    ]
                else:
                    tile = self.world_map.get_tile(x_tile_idx, y_tile_idx)
                    if tile:
                        current_tile_grid, display_type = tile.get_display_info()
                    else:
                        # Should ideally not happen if map is correctly initialized
                        unknown_symbol = TILE_SYMBOLS["unknown"]
                        current_tile_grid = [
                            [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                            [FLOOR_SYMBOL, unknown_symbol, FLOOR_SYMBOL],
                            [FLOOR_SYMBOL, FLOOR_SYMBOL, FLOOR_SYMBOL],
                        ]
                        display_type = "unknown" # Already default, but explicit

                for y_offset in range(3): # Iterate 3 rows of the tile grid
                    y_screen = y_tile_idx * 3 + y_offset
                    # Ensure y_screen is within the map display area (not overlapping UI)
                    if y_screen >= curses.LINES - UI_LINES_BUFFER:
                        # This condition should ideally be caught by max_y_tile_rows,
                        # but as a safeguard, especially if UI_LINES_BUFFER is small.
                        continue 

                    for x_offset in range(3): # Iterate 3 columns of the tile grid
                        x_screen = x_tile_idx * 3 + x_offset
                        # Ensure x_screen is within screen width
                        if x_screen >= curses.COLS -1: # -1 due to curses behavior at rightmost column
                            break # Go to next tile row or finish tile

                        char_to_draw = current_tile_grid[y_offset][x_offset]
                        color_attribute = curses.color_pair(0) # Default

                        if display_type == "wall":
                            color_attribute = curses.color_pair(self.WALL_COLOR_PAIR)
                        elif display_type == "floor":
                            color_attribute = curses.color_pair(self.FLOOR_COLOR_PAIR)
                        else: # Player, Monster, Item, Unknown are on a floor-like background
                            if y_offset == 1 and x_offset == 1: # Center symbol
                                if display_type == "player":
                                    color_attribute = curses.color_pair(self.PLAYER_COLOR_PAIR)
                                elif display_type == "monster":
                                    color_attribute = curses.color_pair(self.MONSTER_COLOR_PAIR)
                                elif display_type == "item":
                                    color_attribute = curses.color_pair(self.ITEM_COLOR_PAIR)
                                else: # Unknown center symbol
                                    color_attribute = curses.color_pair(0) # Default
                            else: # Surrounding symbols for entities
                                color_attribute = curses.color_pair(self.FLOOR_COLOR_PAIR)
                        
                        try:
                            self.stdscr.addstr(y_screen, x_screen, char_to_draw, color_attribute)
                        except curses.error:
                            # Error could occur if char is wide and at edge, or other curses issues.
                            # Break from drawing this specific tile's remainder.
                            # The x_screen and y_screen checks should prevent most of these.
                            break 
                    if x_screen >= curses.COLS -1 and y_offset < 2 : # If broken from x_offset loop early
                        pass # allow y_offset loop to continue to try to draw next line of current tile if space

        # UI elements (HP, mode, messages) are drawn below the map
        # Adjusted Y position for UI elements
        hp_line_y = max_y_tile_rows * 3 

        if hp_line_y < curses.LINES:
            hp_text = f"HP: {self.player.health}"
            try:
                self.stdscr.addstr(hp_line_y, 0, hp_text)
            except curses.error:
                pass # Avoid crash if cannot draw (e.g. screen too small)
        else: # Fallback if map takes all space (or more)
             hp_line_y = curses.LINES - UI_LINES_BUFFER # Try to squeeze it in the reserved area

        mode_line_y = hp_line_y + 1
        if mode_line_y < curses.LINES: # Check if space for mode line
            mode_text = f"MODE: {self.input_mode.upper()}"
            try:
                self.stdscr.addstr(mode_line_y, 0, mode_text)
            except curses.error:
                pass
        else: # Fallback
            mode_line_y = curses.LINES - (UI_LINES_BUFFER -1) if UI_LINES_BUFFER >1 else curses.LINES -1


        message_start_y = mode_line_y + 1
        if self.input_mode == "command":
            if message_start_y < curses.LINES: # Check if space for command prompt
                prompt_text = f"> {self.current_command_buffer}"
                try:
                    self.stdscr.addstr(message_start_y, 0, prompt_text)
                    message_start_y += 1 # Messages start after prompt line
                except curses.error:
                    pass # message_start_y remains as is if prompt fails
        
        # Calculate how many messages can be displayed
        available_lines_for_messages = curses.LINES - message_start_y
        if available_lines_for_messages <= 0:
            num_messages_to_display = 0
        else:
            # Display up to a certain number of recent messages, e.g., 2 or 3
            # depending on UI_LINES_BUFFER and space taken by HP/Mode/Prompt
            max_possible_messages = available_lines_for_messages
            num_messages_to_display = min(len(self.message_log), max_possible_messages)

        start_index = max(0, len(self.message_log) - num_messages_to_display)
        messages_to_display = self.message_log[start_index:]

        for i, message in enumerate(messages_to_display):
            current_message_y = message_start_y + i
            if current_message_y < curses.LINES: # Ensure message fits on screen
                # Truncate message if too long for the screen width
                truncated_message = message
                if len(message) >= curses.COLS: 
                    truncated_message = message[: curses.COLS - 1] 
                try:
                    self.stdscr.addstr(current_message_y, 0, truncated_message)
                except curses.error: 
                    break 
            else: 
                break
        
        if not self.debug_mode:
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
            adjacent_monsters_with_coords = self._get_adjacent_monsters(
                self.player.x, self.player.y
            )
            target_monster = None
            target_x, target_y = -1, -1

            if argument:  # Monster name provided
                named_targets = [
                    (m, mx, my)
                    for m, mx, my in adjacent_monsters_with_coords
                    if m.name.lower() == argument.lower()
                ]
                if len(named_targets) == 1:
                    target_monster, target_x, target_y = named_targets[0]
                elif len(named_targets) > 1:
                    self.message_log.append(f"Multiple {argument}s found. Which one?")
                else:  # No monsters by that name found (either none adjacent, or none with that name)
                    self.message_log.append(
                        f"There is no monster named {argument} nearby."
                    )
            else:  # No monster name provided
                if not adjacent_monsters_with_coords:
                    self.message_log.append("There is no monster nearby to attack.")
                elif len(adjacent_monsters_with_coords) == 1:
                    target_monster, target_x, target_y = adjacent_monsters_with_coords[
                        0
                    ]
                else:  # Multiple monsters, no specific name given
                    monster_names = ", ".join(
                        sorted(
                            list(
                                set(m.name for m, _, _ in adjacent_monsters_with_coords)
                            )
                        )
                    )
                    self.message_log.append(
                        f"Multiple monsters nearby: {monster_names}. Which one to attack?"
                    )

            if target_monster and target_x != -1 and target_y != -1:
                damage_dealt = self.player.attack_monster(target_monster)
                self.message_log.append(
                    f"You attack the {target_monster.name} for {damage_dealt} damage."
                )
                if target_monster.health <= 0:
                    self.world_map.remove_monster(target_x, target_y)
                    self.message_log.append(f"You defeated the {target_monster.name}!")
                else:
                    damage_taken = target_monster.attack(self.player)
                    self.message_log.append(
                        f"The {target_monster.name} attacks you for {damage_taken} damage."
                    )
                    if self.player.health <= 0:
                        self.message_log.append("You have been defeated. Game Over.")
                        self.game_over = True
            # If no target_monster was identified by the logic above, an appropriate message
            # should have already been added to self.message_log.

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
                # Also list adjacent monsters for "look"
                adjacent_monsters_with_coords = self._get_adjacent_monsters(
                    self.player.x, self.player.y
                )
                if adjacent_monsters_with_coords:
                    for m, x, y in adjacent_monsters_with_coords:
                        self.message_log.append(f"You see a {m.name} at ({x}, {y}).")
                elif (
                    not tile.item and not tile.monster
                ):  # only if no item/monster on current tile AND no adjacent monsters
                    self.message_log.append("The area is clear.")

        elif verb == "quit":  # This is if "quit" is typed as a command
            self.message_log.append("Quitting game.")
            self.game_over = True

    def _get_adjacent_monsters(
        self, x: int, y: int
    ) -> list[tuple["Monster", int, int]]:
        adjacent_monsters = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # N, S, W, E
            adj_x, adj_y = x + dx, y + dy
            tile = self.world_map.get_tile(adj_x, adj_y)
            if tile and tile.monster:
                adjacent_monsters.append((tile.monster, adj_x, adj_y))
        return adjacent_monsters

    def run(self):
        if self.debug_mode:
            print(
                "Error: GameEngine.run() called in debug_mode. Use main_debug() in main.py for testing."
            )
            return

        try:
            self.render_map()
            while not self.game_over:
                parsed_command_output = self.handle_input_and_get_command()
                if parsed_command_output:
                    self.process_command_tuple(parsed_command_output)
                self.render_map()

            self.render_map()  # Final render before potential napms
            if self.game_over:
                curses.napms(2000)  # Pause to show final game state/message
        finally:
            if not self.debug_mode and hasattr(self, "stdscr") and self.stdscr:
                self.stdscr.keypad(False)
                curses.echo()
                curses.nocbreak()
                curses.endwin()

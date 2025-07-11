import curses
import time

from src.ai_logic import AILogic
from src.command_processor import CommandProcessor  # Import CommandProcessor
from src.input_handler import InputHandler
from src.message_log import MessageLog

# Assuming these are first-party imports
from src.parser import Parser
from src.player import Player
from src.renderer import Renderer  # Import Renderer
from src.world_generator import WorldGenerator
from src.world_map import WorldMap  # Added for AI visible map

# Monster class is forward-declared as a string literal in type hints


class GameEngine:
    """
    Manages the main game loop, game state, and interactions between different
    game components like the WorldGenerator, Player, Renderer, InputHandler,
    and CommandProcessor.
    """

    def __init__(
        self,
        map_width: int = 20,
        map_height: int = 10,
        debug_mode: bool = False,
        ai_active: bool = False,
        ai_sleep_duration: float = 0.5,
    ):
        """
        Initializes the game engine and its components.

        Args:
            map_width: The width of the game map.
            map_height: The height of the game map.
            debug_mode: If True, the game runs in a mode suitable for debugging
                        (e.g., without curses screen initialization).
            ai_active: If True, AI controls the player.
            ai_sleep_duration: Time in seconds AI waits between actions.
        """
        self.world_generator = WorldGenerator()
        self.parser = Parser()
        self.debug_mode = debug_mode
        self.ai_active = ai_active
        self.ai_sleep_duration = ai_sleep_duration
        self.ai_logic = None
        self.visible_map = None  # Will hold the AI's or player's known map

        # Player symbol is now defined and passed to Renderer directly.

        # Generate the game world, player starting position, and winning position.
        # This is the "real" map.
        self.world_map, player_start_pos, self.winning_position = (
            self.world_generator.generate_map(
                map_width, map_height, seed=None
            )  # Consider making seed configurable for testing
        )

        # Create the visible map for fog of war.
        # This map represents what the player or AI can currently see.
        # It has the same dimensions as the real map.
        # Initially, all tiles will have tile.is_explored = False (default for Tile).
        self.visible_map = WorldMap(
            width=self.world_map.width, height=self.world_map.height
        )

        # Instantiate Renderer first (handles curses init if not debug_mode).
        player_symbol = "@"  # Define the player's visual representation on the map.
        self.renderer = Renderer(
            debug_mode=self.debug_mode,
            map_width=self.world_map.width,
            map_height=self.world_map.height,
            player_symbol=player_symbol,
        )

        # Instantiate InputHandler, passing stdscr from the renderer.
        self.input_handler = InputHandler(self.renderer.stdscr, self.parser)

        self.command_processor = CommandProcessor()

        # Initialize the player at the starting position with default health.
        self.player = Player(x=player_start_pos[0], y=player_start_pos[1], health=20)
        self.game_over = False  # Flag to control the main game loop.
        self.message_log = MessageLog(max_messages=5)  # Use MessageLog class

        if self.ai_active:
            # Initialize AI logic if AI is active.
            # AI will use the same visible_map.
            self.ai_logic = AILogic(
                player=self.player,
                real_world_map=self.world_map,
                ai_visible_map=self.visible_map,  # AI uses the unified visible_map
                message_log=self.message_log,
            )
            # AI's own update_visibility will be called at the start of its turn.

        # Initial visibility update for the player's starting position.
        self._update_fog_of_war_visibility()

    def _update_fog_of_war_visibility(self) -> None:
        """
        Updates the player's visible map based on their current position.
        Reveals tiles in a 1-tile radius (8 directions + current tile).
        """
        player_x, player_y = self.player.x, self.player.y

        for dy_offset in range(-1, 2):  # Iterates from -1 to 1 (inclusive)
            for dx_offset in range(-1, 2):  # Iterates from -1 to 1 (inclusive)
                map_x, map_y = player_x + dx_offset, player_y + dy_offset

                # Check if the coordinates are within the bounds of the real map
                if (
                    0 <= map_x < self.world_map.width
                    and 0 <= map_y < self.world_map.height
                ):
                    real_tile = self.world_map.get_tile(map_x, map_y)
                    if real_tile:
                        # Get the corresponding tile in the player's visible map
                        visible_tile = self.visible_map.get_tile(map_x, map_y)
                        if visible_tile:
                            # Copy data from real tile to visible tile
                            visible_tile.type = real_tile.type
                            # Important: Copy monster and item *references*.
                            # If they are mutable and change (e.g. monster moves,
                            # item taken), the visible map should reflect this if
                            # the tile remains explored.
                            visible_tile.monster = real_tile.monster
                            visible_tile.item = real_tile.item
                            visible_tile.is_explored = True  # Mark as explored

    # Note: Methods like handle_input_and_get_command, render_map,
    # process_command_tuple, and _get_adjacent_monsters were removed.
    # Their responsibilities have been moved to InputHandler, Renderer,
    # and CommandProcessor respectively.

    def run(self):
        """
        Starts and manages the main game loop.
        Handles input, processes commands, and renders the game state
        until the game is over.
        """
        if self.debug_mode:
            # Special handling for debug mode to prevent curses initialization
            # and allow for simpler testing via main_debug().
            print(
                "Error: GameEngine.run() called in debug_mode. "
                "Use main_debug() in main.py for testing."
            )
            self.game_over = True  # Set game_over for test conditions.
            # Perform a single render to list for debug inspection, as per some tests.
            # Update visibility before rendering, even in debug mode.
            self._update_fog_of_war_visibility()
            current_ai_path_debug = None
            if self.ai_active and self.ai_logic:
                current_ai_path_debug = self.ai_logic.current_path
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=self.visible_map,  # Always use visible_map
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=True,  # Ensure output is to list for debug
                ai_path=current_ai_path_debug,
            )
            return

        try:
            # Initial visibility update (already done in __init__, but good
            # practice if run is called separately)
            self._update_fog_of_war_visibility()
            # Initial render of the game state before the loop starts.
            current_ai_path_initial = None
            if self.ai_active and self.ai_logic:
                current_ai_path_initial = self.ai_logic.current_path
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=self.visible_map,  # Always use visible_map
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # Should be False here for curses
                ai_path=current_ai_path_initial,
            )

            while not self.game_over:
                # Update visibility at the start of each turn.
                # AILogic also calls its own visibility update, which is fine
                # as it uses the same visible_map.
                self._update_fog_of_war_visibility()

                # Handle player input or AI action.
                parsed_command_output = None
                if self.ai_active and self.ai_logic:
                    if self.ai_sleep_duration > 0:
                        time.sleep(self.ai_sleep_duration)
                    # AI's get_next_action internally calls its update_visibility
                    # on the shared visible_map.
                    parsed_command_output = self.ai_logic.get_next_action()
                else:
                    # Player input
                    parsed_command_output = (
                        self.input_handler.handle_input_and_get_command()
                    )

                if parsed_command_output:
                    if self.game_over:
                        self.message_log.add_message("The game is over.")
                    else:
                        results = self.command_processor.process_command(
                            parsed_command_output,
                            self.player,
                            self.world_map,  # Commands affect the real map
                            self.message_log,
                            self.winning_position,
                        )
                        self.game_over = results.get("game_over", False)

                        # After a command (especially move), update visibility
                        # again before rendering.
                        # This ensures that if a player moves, the new view is
                        # immediately reflected.
                        if not self.game_over:  # No need to update if game just ended
                            self._update_fog_of_war_visibility()

                # Render updated game state.
                current_ai_path = None
                if self.ai_active and self.ai_logic:
                    current_ai_path = self.ai_logic.current_path

                self.renderer.render_all(
                    player_x=self.player.x,
                    player_y=self.player.y,
                    player_health=self.player.health,
                    world_map_to_render=self.visible_map,  # Always use visible_map
                    input_mode=self.input_handler.get_input_mode(),
                    current_command_buffer=self.input_handler.get_command_buffer(),
                    message_log=self.message_log,
                    debug_render_to_list=self.debug_mode,
                    ai_path=current_ai_path,
                )

            # After the game loop ends (game_over is True):
            # Perform a final visibility update and render to show the game over state.
            self._update_fog_of_war_visibility()
            current_ai_path_final = None
            if self.ai_active and self.ai_logic:
                current_ai_path_final = self.ai_logic.current_path

            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=self.visible_map,  # Always use visible_map
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # Should be False here
                ai_path=current_ai_path_final,
            )

            # Pause briefly to let the player see the final game over screen.
            if self.game_over and not self.debug_mode:
                curses.napms(2000)  # Pause for 2 seconds.
        finally:
            # Ensure curses is cleaned up properly, but only if not in debug mode.
            if not self.debug_mode:
                self.renderer.cleanup_curses()

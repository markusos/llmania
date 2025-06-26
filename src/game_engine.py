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
        self.ai_visible_map = None  # Will hold the AI's known map

        # Player symbol is now defined and passed to Renderer directly.

        # Generate the game world, player starting position, and winning position.
        # This is the "real" map.
        self.world_map, player_start_pos, self.winning_position = (
            self.world_generator.generate_map(
                map_width, map_height, seed=None
            )  # Consider making seed configurable for testing
        )

        if self.ai_active:
            # Create a separate map for what the AI can see.
            # It has the same dimensions as the real map.
            # Initially, all tiles in ai_visible_map will have tile.is_explored = False.
            # The default Tile initializer sets is_explored to False.
            # The default tile_type is "floor", which is fine; rendering will handle fog.
            self.ai_visible_map = WorldMap(
                width=self.world_map.width, height=self.world_map.height
            )
            # Optional: Could explicitly set all ai_visible_map tiles to a specific "fog" type here
            # for y in range(self.ai_visible_map.height):
            #     for x in range(self.ai_visible_map.width):
            #         tile = self.ai_visible_map.get_tile(x,y)
            #         if tile:
            #             tile.type = "fog" # A hypothetical type, if we use it over is_explored for rendering
            #             tile.is_explored = False
            # However, relying on is_explored = False and the Renderer handling it is simpler.

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
            if not self.ai_visible_map:  # Should have been created above
                # This case should ideally not be reached if logic is correct.
                # Fallback: create it now, though it's better to ensure it's created before Renderer.
                self.ai_visible_map = WorldMap(
                    width=self.world_map.width, height=self.world_map.height
                )

            self.ai_logic = AILogic(
                player=self.player,
                real_world_map=self.world_map,  # Pass the actual map
                ai_visible_map=self.ai_visible_map,  # Pass the AI's map
                message_log=self.message_log,
            )
            # Initial visibility update for AI's starting position
            self.ai_logic.update_visibility()

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
            map_to_render_debug = (
                self.ai_visible_map
                if self.ai_active and self.ai_visible_map
                else self.world_map
            )
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=map_to_render_debug,  # Pass correct map
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=True,  # Ensure output is to list for debug
                ai_mode_active=self.ai_active,  # Pass AI mode status
            )
            return

        try:
            # Initial render of the game state before the loop starts.
            initial_map_to_render = (
                self.ai_visible_map
                if self.ai_active and self.ai_visible_map
                else self.world_map
            )
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=initial_map_to_render,  # Pass correct map
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # Should be False here for curses
                ai_mode_active=self.ai_active,  # Pass AI mode status
            )

            while not self.game_over:
                # Handle player input and parse it into a command.
                parsed_command_output = None
                if self.ai_active and self.ai_logic:
                    if self.ai_sleep_duration > 0:
                        time.sleep(self.ai_sleep_duration)
                    # Pass the current game state to get_next_action.
                    # AILogic has player, world_map, message_log from its init.
                    # More dynamic info can be passed here if needed in the future.
                    parsed_command_output = self.ai_logic.get_next_action()

                    # Optional: Log AI thinking/acting. (e.g., "AI is pondering...")
                    # This might make the log noisy, consider if it's needed.
                else:
                    parsed_command_output = (
                        self.input_handler.handle_input_and_get_command()
                    )

                if parsed_command_output:
                    # self.message_log.clear() # Removed: MessageLog handles history

                    # If the game is already marked as over (e.g., by a previous command
                    # that allows further input before full loop termination),
                    # just show a message.
                    if self.game_over:
                        self.message_log.add_message(
                            "The game is over."
                        )  # Use add_message
                    else:
                        # Process command and get results (e.g., if game is now over).
                        results = self.command_processor.process_command(
                            parsed_command_output,
                            self.player,
                            self.world_map,
                            self.message_log,
                            self.winning_position,
                        )
                        self.game_over = results.get("game_over", False)

                # Render updated game state after command (or if no command).
                map_to_render_loop = (
                    self.ai_visible_map
                    if self.ai_active and self.ai_visible_map
                    else self.world_map
                )
                self.renderer.render_all(
                    player_x=self.player.x,
                    player_y=self.player.y,
                    player_health=self.player.health,
                    world_map_to_render=map_to_render_loop,  # Pass correct map
                    input_mode=self.input_handler.get_input_mode(),
                    current_command_buffer=self.input_handler.get_command_buffer(),
                    message_log=self.message_log,
                    debug_render_to_list=self.debug_mode,  # Should be False here
                    ai_mode_active=self.ai_active,  # Pass AI mode status
                )

            # After the game loop ends (game_over is True):
            # Perform a final render to show the game over state.
            final_map_to_render = (
                self.ai_visible_map
                if self.ai_active and self.ai_visible_map
                else self.world_map
            )
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=final_map_to_render,  # Pass correct map
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # Should be False here
                ai_mode_active=self.ai_active,  # Pass AI mode status
            )

            # Pause briefly to let the player see the final game over screen.
            if self.game_over and not self.debug_mode:
                curses.napms(2000)  # Pause for 2 seconds.
        finally:
            # Ensure curses is cleaned up properly, but only if not in debug mode.
            if not self.debug_mode:
                self.renderer.cleanup_curses()

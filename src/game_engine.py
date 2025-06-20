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
        # Player symbol is now defined and passed to Renderer directly.

        # Generate the game world, player starting position, and winning position.
        self.world_map, player_start_pos, self.winning_position = (
            self.world_generator.generate_map(
                map_width, map_height, seed=None
            )  # Consider making seed configurable for testing
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
            self.ai_logic = AILogic(
                player=self.player,
                world_map=self.world_map,
                message_log=self.message_log,
            )

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
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map=self.world_map,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=True,  # Ensure output is to list for debug
            )
            return

        try:
            # Initial render of the game state before the loop starts.
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map=self.world_map,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # Should be False here for curses
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
                self.renderer.render_all(
                    player_x=self.player.x,
                    player_y=self.player.y,
                    player_health=self.player.health,
                    world_map=self.world_map,
                    input_mode=self.input_handler.get_input_mode(),
                    current_command_buffer=self.input_handler.get_command_buffer(),
                    message_log=self.message_log,
                    debug_render_to_list=self.debug_mode,  # Should be False here
                )

            # After the game loop ends (game_over is True):
            # Perform a final render to show the game over state.
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map=self.world_map,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # Should be False here
            )

            # Pause briefly to let the player see the final game over screen.
            if self.game_over and not self.debug_mode:
                curses.napms(2000)  # Pause for 2 seconds.
        finally:
            # Ensure curses is cleaned up properly, but only if not in debug mode.
            if not self.debug_mode:
                self.renderer.cleanup_curses()

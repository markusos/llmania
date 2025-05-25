import curses

from src.command_processor import CommandProcessor  # Import CommandProcessor
from src.input_handler import InputHandler

# Assuming these are first-party imports
from src.parser import Parser
from src.player import Player
from src.renderer import Renderer  # Import Renderer
from src.world_generator import WorldGenerator

# Monster class is forward-declared as a string literal in type hints


class GameEngine:
    def __init__(
        self, map_width: int = 20, map_height: int = 10, debug_mode: bool = False
    ):
        self.world_generator = WorldGenerator()
        self.parser = Parser()
        self.debug_mode = debug_mode
        # self.PLAYER_SYMBOL = "@" # Removed

        if not self.debug_mode:
            self.stdscr = curses.initscr()
            # curses.start_color() # Moved to Renderer
            curses.noecho()  # Moved to Renderer (effectively, as Renderer does it)
            curses.cbreak()  # Moved to Renderer (effectively, as Renderer does it)
            self.stdscr.keypad(
                True
            )  # Moved to Renderer (effectively, as Renderer does it)
            # curses.curs_set(0)   # Moved to Renderer
            # Color pair initializations removed
        else:
            self.stdscr = None
            # Removed color pair defaults as they are handled by Renderer's else block

        self.world_map, player_start_pos, self.win_pos = (
            self.world_generator.generate_map(map_width, map_height, seed=None)
        )
        # Instantiate InputHandler after stdscr might be initialized
        self.input_handler = InputHandler(self.stdscr, self.parser)
        # Instantiate Renderer after stdscr and world_map are initialized
        player_symbol = "@"  # Define player symbol locally for renderer
        self.renderer = Renderer(
            self.stdscr, self.world_map.width, self.world_map.height, player_symbol
        )
        self.command_processor = CommandProcessor()  # Instantiate CommandProcessor

        self.player = Player(x=player_start_pos[0], y=player_start_pos[1], health=20)
        self.game_over = False
        self.message_log = []

    # handle_input_and_get_command method is removed
    # render_map method is removed
    # process_command_tuple method is removed
    # _get_adjacent_monsters method is removed

    def run(self):
        if self.debug_mode:
            print(
                "Error: GameEngine.run() called in debug_mode. "
                "Use main_debug() in main.py for testing."
            )
            return
        try:
            # Initial render
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map=self.world_map,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # For list rendering
            )
            while not self.game_over:
                parsed_command_output = (
                    self.input_handler.handle_input_and_get_command()
                )
                if parsed_command_output:
                    # Clear message log before processing new command
                    self.message_log.clear()
                    # Check if game is already over before processing
                    if self.game_over:
                        self.message_log.append("The game is over.")
                    else:
                        results = self.command_processor.process_command(
                            parsed_command_output,
                            self.player,
                            self.world_map,
                            self.message_log,
                            self.win_pos,
                        )
                        self.game_over = results.get("game_over", False)

                self.renderer.render_all(
                    player_x=self.player.x,
                    player_y=self.player.y,
                    player_health=self.player.health,
                    world_map=self.world_map,
                    input_mode=self.input_handler.get_input_mode(),
                    current_command_buffer=self.input_handler.get_command_buffer(),
                    message_log=self.message_log,
                    debug_render_to_list=self.debug_mode,  # For list rendering
                )

            # Final render after game over
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map=self.world_map,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,  # For list rendering
            )

            if self.game_over and not self.debug_mode:  # napms only if not in debug
                curses.napms(2000)
        finally:
            if not self.debug_mode:  # Cleanup only if not in debug
                self.renderer.cleanup_curses()

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

        # world_map and visible_map will be dictionaries: floor_id -> WorldMap
        self.world_maps: dict[int, WorldMap] = {}
        self.visible_maps: dict[int, WorldMap] = {}

        # Player symbol is defined and passed to Renderer directly.

        # Generate the game world: multiple floors, player start (x,y,floor_id),
        # and win position (x,y,floor_id).
        # This will use the new generate_world method.
        # NOTE: This line will be uncommented/updated when generate_world is fully ready
        # and its return signature matches.
        # For now, using placeholder for single floor from old generate_map:
        # self.world_maps, player_start_full_pos, self.winning_full_pos = \
        #     self.world_generator.generate_world(map_width, map_height, seed=None)

        temp_single_map, temp_player_start_coords, temp_winning_coords = (
            self.world_generator._generate_single_floor(
                map_width, map_height, current_seed=None
            )
        )  # Changed to _generate_single_floor

        self.world_maps = {0: temp_single_map}  # Initialize with one floor
        player_start_full_pos = (
            temp_player_start_coords[0],
            temp_player_start_coords[1],
            0,
        )
        self.winning_full_pos = (temp_winning_coords[0], temp_winning_coords[1], 0)

        # Create a visible map for each floor.
        self.visible_maps: dict[int, WorldMap] = {}
        for floor_id, w_map in self.world_maps.items():
            self.visible_maps[floor_id] = WorldMap(
                width=w_map.width, height=w_map.height
            )

        # Renderer map dimensions are based on floor 0.
        # Assumes fixed map size for now.
        player_symbol = "@"
        self.renderer = Renderer(
            debug_mode=self.debug_mode,
            map_width=self.world_maps[0].width,
            map_height=self.world_maps[0].height,
            player_symbol=player_symbol,
        )

        self.input_handler = InputHandler(self.renderer.stdscr, self.parser)
        self.command_processor = CommandProcessor()

        # Initialize the player with x, y, and current_floor_id.
        self.player = Player(
            x=player_start_full_pos[0],
            y=player_start_full_pos[1],
            current_floor_id=player_start_full_pos[2],
            health=20,
        )
        self.game_over = False
        self.message_log = MessageLog(max_messages=5)

        if self.ai_active:
            self.ai_logic = AILogic(
                player=self.player,
                # Pass the dictionaries of maps to AI
                real_world_maps=self.world_maps,
                ai_visible_maps=self.visible_maps,
                message_log=self.message_log,
            )

        self._update_fog_of_war_visibility()

    def _update_fog_of_war_visibility(self) -> None:
        """
        Updates the player's visible map for the current floor based on their position.
        Reveals tiles in a 1-tile radius.
        """
        player_x, player_y = self.player.x, self.player.y
        current_floor_id = self.player.current_floor_id

        current_real_map = self.world_maps.get(current_floor_id)
        current_visible_map = self.visible_maps.get(current_floor_id)

        if not current_real_map or not current_visible_map:
            self.message_log.add_message(
                f"Error: Invalid floor ID {current_floor_id} for visibility."
            )
            return

        for dy_offset in range(-1, 2):
            for dx_offset in range(-1, 2):
                map_x, map_y = player_x + dx_offset, player_y + dy_offset

                if not (
                    0 <= map_x < current_real_map.width
                    and 0 <= map_y < current_real_map.height
                ):
                    continue

                real_tile = current_real_map.get_tile(map_x, map_y)
                if real_tile:
                    visible_tile = current_visible_map.get_tile(map_x, map_y)
                    if visible_tile:
                        # Copy relevant attributes from real tile to visible tile
                        visible_tile.type = real_tile.type
                        visible_tile.monster = real_tile.monster
                        visible_tile.item = real_tile.item
                        visible_tile.is_portal = real_tile.is_portal
                        visible_tile.portal_to_floor_id = real_tile.portal_to_floor_id
                        visible_tile.is_explored = True

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
            current_visible_map_for_render = self.visible_maps.get(
                self.player.current_floor_id
            )
            if not current_visible_map_for_render:
                # Fallback to floor 0 or handle error more gracefully.
                current_visible_map_for_render = self.visible_maps.get(
                    0, WorldMap(self.renderer.map_width, self.renderer.map_height)
                )

            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=current_visible_map_for_render,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=True,
                ai_path=current_ai_path_debug,
                current_floor_id=self.player.current_floor_id,  # Pass current floor ID
            )
            return

        try:
            self._update_fog_of_war_visibility()
            current_ai_path_initial = None
            if self.ai_active and self.ai_logic:
                current_ai_path_initial = self.ai_logic.current_path

            initial_visible_map = self.visible_maps.get(self.player.current_floor_id)
            if not initial_visible_map:
                initial_visible_map = self.visible_maps.get(
                    0, WorldMap(self.renderer.map_width, self.renderer.map_height)
                )

            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=initial_visible_map,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,
                ai_path=current_ai_path_initial,
                current_floor_id=self.player.current_floor_id,
            )

            while not self.game_over:
                self._update_fog_of_war_visibility()
                parsed_command_output = None
                if self.ai_active and self.ai_logic:
                    if self.ai_sleep_duration > 0:
                        time.sleep(self.ai_sleep_duration)
                    parsed_command_output = self.ai_logic.get_next_action()
                else:
                    parsed_command_output = (
                        self.input_handler.handle_input_and_get_command()
                    )

                if parsed_command_output:
                    if self.game_over:  # Should not process if already over
                        self.message_log.add_message("The game is over.")
                    else:
                        results = self.command_processor.process_command(
                            parsed_command_output,
                            self.player,
                            self.world_maps,
                            self.message_log,
                            self.winning_full_pos,
                            game_engine=self,
                        )
                        self.game_over = results.get("game_over", False)
                        if not self.game_over:
                            # Crucial after floor change
                            self._update_fog_of_war_visibility()

                current_ai_path_loop = (
                    self.ai_logic.current_path
                    if self.ai_active and self.ai_logic
                    else None
                )
                loop_visible_map = self.visible_maps.get(self.player.current_floor_id)
                if not loop_visible_map:
                    loop_visible_map = self.visible_maps.get(
                        0, WorldMap(self.renderer.map_width, self.renderer.map_height)
                    )
                self.renderer.render_all(
                    player_x=self.player.x,
                    player_y=self.player.y,
                    player_health=self.player.health,
                    world_map_to_render=loop_visible_map,
                    input_mode=self.input_handler.get_input_mode(),
                    current_command_buffer=self.input_handler.get_command_buffer(),
                    message_log=self.message_log,
                    debug_render_to_list=self.debug_mode,
                    ai_path=current_ai_path_loop,
                    current_floor_id=self.player.current_floor_id,
                )

            # Final render after game over
            self._update_fog_of_war_visibility()
            current_ai_path_final = (
                self.ai_logic.current_path if self.ai_active and self.ai_logic else None
            )
            final_visible_map = self.visible_maps.get(self.player.current_floor_id)
            if not final_visible_map:
                final_visible_map = self.visible_maps.get(
                    0, WorldMap(self.renderer.map_width, self.renderer.map_height)
                )
            self.renderer.render_all(
                player_x=self.player.x,
                player_y=self.player.y,
                player_health=self.player.health,
                world_map_to_render=final_visible_map,
                input_mode=self.input_handler.get_input_mode(),
                current_command_buffer=self.input_handler.get_command_buffer(),
                message_log=self.message_log,
                debug_render_to_list=self.debug_mode,
                ai_path=current_ai_path_final,
                current_floor_id=self.player.current_floor_id,
            )
            if self.game_over and not self.debug_mode:
                curses.napms(2000)  # Pause for 2 seconds.
        finally:
            # Ensure curses is cleaned up properly, but only if not in debug mode.
            if not self.debug_mode:
                self.renderer.cleanup_curses()

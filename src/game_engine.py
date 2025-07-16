import curses
import random
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
        seed: int | None = None,
        verbose: int = 0,
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
            seed: Optional seed for random number generation to ensure
                  reproducibility.
            verbose: Verbosity level for debug output.
        """
        self.world_generator = WorldGenerator()
        self.parser = Parser()
        self.debug_mode = debug_mode
        self.ai_active = ai_active
        self.ai_sleep_duration = ai_sleep_duration
        self.ai_logic = None
        self.verbose = verbose
        self.random = random.Random(seed)

        # world_map and visible_map will be dictionaries: floor_id -> WorldMap
        self.world_maps: dict[int, WorldMap] = {}
        self.visible_maps: dict[int, WorldMap] = {}

        # Player symbol is defined and passed to Renderer directly.

        # Generate the game world: multiple floors, player start (x,y,floor_id),
        # and win position (x,y,floor_id).
        # This will use the new generate_world method.
        (
            self.world_maps,
            player_start_full_pos,
            self.winning_full_pos,
            _floor_details_list,
        ) = self.world_generator.generate_world(
            map_width, map_height, random_generator=self.random
        )

        # Create a visible map for each floor.
        for floor_id, w_map in self.world_maps.items():
            self.visible_maps[floor_id] = WorldMap(
                width=w_map.width, height=w_map.height
            )

        first_floor_id = min(self.world_maps.keys()) if self.world_maps else 0
        render_map_width = (
            self.world_maps[first_floor_id].width if self.world_maps else map_width
        )
        render_map_height = (
            self.world_maps[first_floor_id].height if self.world_maps else map_height
        )

        player_symbol = "@"
        self.renderer = Renderer(
            debug_mode=self.debug_mode,
            map_width=render_map_width,
            map_height=render_map_height,
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
                real_world_maps=self.world_maps,
                ai_visible_maps=self.visible_maps,
                message_log=self.message_log,
                random_generator=self.random,
                verbose=self.verbose,
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
                        visible_tile.type = real_tile.type
                        visible_tile.monster = real_tile.monster
                        visible_tile.item = real_tile.item
                        visible_tile.is_portal = real_tile.is_portal
                        visible_tile.portal_to_floor_id = real_tile.portal_to_floor_id
                        visible_tile.is_explored = True

    def run(self):
        """
        Starts and manages the main game loop.
        """
        if self.debug_mode:
            self.run_debug_mode()
            return

        try:
            self._update_fog_of_war_visibility()
            current_ai_path_initial = None
            ai_state = None
            if self.ai_active and self.ai_logic:
                current_ai_path_initial = self.ai_logic.current_path
                ai_state = self.ai_logic.state.__class__.__name__

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
                ai_state=ai_state,
            )

            while not self.game_over:
                self._handle_invisibility()
                self._update_fog_of_war_visibility()
                parsed_command_output = None
                if self.ai_active and self.ai_logic:
                    if self.ai_sleep_duration > 0:
                        time.sleep(self.ai_sleep_duration)
                    parsed_command_output = self.ai_logic.get_next_action()
                    ai_state = self.ai_logic.state.__class__.__name__
                else:
                    parsed_command_output = (
                        self.input_handler.handle_input_and_get_command()
                    )

                if parsed_command_output:
                    if self.game_over:
                        self.message_log.add_message("The game is over.")
                    else:
                        floor_before_command = self.player.current_floor_id
                        results = self.command_processor.process_command(
                            parsed_command_output,
                            self.player,
                            self.world_maps,
                            self.message_log,
                            self.winning_full_pos,
                            game_engine=self,
                        )
                        if "used_item" in results:
                            self._handle_item_use(results["used_item"])
                        floor_after_command = self.player.current_floor_id
                        if (
                            self.ai_active
                            and self.ai_logic
                            and floor_before_command != floor_after_command
                        ):
                            self.ai_logic.current_path = None
                            self.message_log.add_message(
                                "AI: Floor changed, clearing path."
                            )

                        self.game_over = results.get("game_over", False)
                        if not self.game_over:
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
                    ai_state=ai_state,
                )

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
                ai_state=ai_state,
            )
            if self.game_over and not self.debug_mode:
                curses.napms(2000)
        finally:
            if not self.debug_mode:
                self.renderer.cleanup_curses()

    def run_debug_mode(self):
        """
        Runs the game in a debug mode without the curses interface.
        This allows for printing game state and messages directly to the console,
        which is useful for testing game logic and content generation.
        """
        print("--- Starting Game in Debug Mode ---")

        print("\n--- Initial Player and Map State ---")
        print(f"Player initial position: ({self.player.x}, {self.player.y})")
        print(f"Player initial health: {self.player.health}")
        print(f"Winning position: {self.winning_full_pos}")
        self._print_full_map_debug()

        # Run the game loop until the game is over
        start_time = time.time()
        timeout_seconds = 30
        self._update_fog_of_war_visibility()
        ai_state = None
        while not self.game_over:
            if time.time() - start_time > timeout_seconds:
                print("--- Debug Mode Timeout ---")
                self.game_over = True
                break
            if self.ai_active and self.ai_logic:
                # Update visibility before AI action
                self._update_fog_of_war_visibility()
                parsed_command_output = self.ai_logic.get_next_action()
                ai_state = self.ai_logic.state.__class__.__name__
                if parsed_command_output:
                    floor_before_command = self.player.current_floor_id
                    results = self.command_processor.process_command(
                        parsed_command_output,
                        self.player,
                        self.world_maps,
                        self.message_log,
                        self.winning_full_pos,
                        game_engine=self,
                    )
                    self.game_over = results.get("game_over", False)
                    floor_after_command = self.player.current_floor_id
                    if floor_before_command != floor_after_command:
                        self.ai_logic.current_path = None
            else:
                # If not AI, we need a way to end the loop in debug.
                self.game_over = True

        print("\n--- Game Over ---")
        # Final state output
        final_map = self.renderer.render_all(
            player_x=self.player.x,
            player_y=self.player.y,
            player_health=self.player.health,
            world_map_to_render=self.visible_maps.get(
                self.player.current_floor_id, self.world_maps[0]
            ),
            input_mode=self.input_handler.get_input_mode(),
            current_command_buffer=self.input_handler.get_command_buffer(),
            message_log=self.message_log,
            debug_render_to_list=True,
            ai_path=self.ai_logic.current_path if self.ai_logic else None,
            current_floor_id=self.player.current_floor_id,
            ai_state=ai_state,
        )
        if final_map:
            for row in final_map:
                print(row)

        print("\n--- Final Messages ---")
        for msg in self.message_log.messages:
            print(msg)

        print("\n--- Debug Mode Finished ---")

    def _handle_item_use(self, item):
        """
        Handles the effects of using an item.
        """
        item_type = item.properties.get("type")
        if item_type == "teleport":
            self._teleport_player()
        elif item_type == "damage":
            self._handle_damage_item(item)

    def _teleport_player(self):
        """
        Teleports the player to a random walkable tile on the current floor.
        """
        current_map = self.world_maps[self.player.current_floor_id]
        walkable_tiles = [
            (x, y)
            for y in range(current_map.height)
            for x in range(current_map.width)
            if current_map.get_tile(x, y).type == "floor"
        ]
        if walkable_tiles:
            self.player.x, self.player.y = self.random.choice(walkable_tiles)
            self.message_log.add_message("You were teleported to a new location.")
            self._update_fog_of_war_visibility()

    def _handle_damage_item(self, item):
        """
        Handles the effects of a damage item.
        """
        self.message_log.add_message(f"You can throw the {item.name}.")
        # The actual throwing logic will be handled by a "throw" command
        # that is not yet implemented.

    def _handle_invisibility(self):
        """
        Handles the player's invisibility status.
        """
        if self.player.invisibility_turns > 0:
            self.player.invisibility_turns -= 1
            if self.player.invisibility_turns == 0:
                self.message_log.add_message("You are no longer invisible.")

    def _print_full_map_debug(self):
        """
        Prints the full map layout for each floor, including portal connections.
        """
        print("\n--- World Map Layout ---")
        for floor_id, world_map in sorted(self.world_maps.items()):
            print(f"\n--- Floor {floor_id} ---")
            portal_info = []
            for y in range(world_map.height):
                for x in range(world_map.width):
                    tile = world_map.get_tile(x, y)
                    if tile and tile.is_portal:
                        portal_info.append(
                            f"Portal at ({x}, {y}) -> Floor {tile.portal_to_floor_id}"
                        )

            # Render the map to a list of strings
            map_render = self.renderer.render_all(
                player_x=-1,  # No player shown
                player_y=-1,
                player_health=0,
                world_map_to_render=world_map,
                input_mode="",
                current_command_buffer="",
                message_log=self.message_log,  # Empty for this purpose
                debug_render_to_list=True,
                current_floor_id=floor_id,
                apply_fog=False,  # Render the whole map regardless of exploration
            )
            if map_render:
                for row in map_render:
                    print(row)

            if portal_info:
                print("Portals:")
                for info in portal_info:
                    print(f"- {info}")

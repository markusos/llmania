from __future__ import annotations

import curses
import random
import time

from src.ai_logic import AILogic
from src.command_processor import CommandProcessor
from src.game_state import GameState
from src.input_handler import InputHandler
from src.message_log import MessageLog
from src.monster_ai.main import MonsterAILogic
from src.parser import Parser
from src.player import Player
from src.renderer import Renderer
from src.world_generator import WorldGenerator
from src.world_map import WorldMap


class GameEngine:
    def __init__(
        self,
        map_width: int = 20,
        map_height: int = 10,
        debug_mode: bool = False,
        ai_active: bool = False,
        ai_sleep_duration: float = 0.5,
        seed: int | None = None,
        verbose: int = 0,
        world_maps: dict[int, WorldMap] | None = None,
        player_start_pos: tuple[int, int, int] | None = None,
        winning_pos: tuple[int, int, int] | None = None,
    ):
        self.world_generator = WorldGenerator()
        self.parser = Parser()
        self.debug_mode = debug_mode
        self.ai_active = ai_active
        self.ai_sleep_duration = ai_sleep_duration
        self.ai_logic = None
        self.verbose = verbose
        self.random = random.Random(seed)

        self.visible_maps: dict[int, WorldMap] = {}

        if world_maps:
            self.world_maps = world_maps
            player_start_full_pos = player_start_pos or (
                map_width // 2,
                map_height // 2,
                0,
            )
            self.winning_full_pos = winning_pos or (0, 0, -1)
        else:
            (
                self.world_maps,
                player_start_full_pos,
                self.winning_full_pos,
                _floor_details_list,
            ) = self.world_generator.generate_world(
                map_width, map_height, random_generator=self.random
            )

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

        self.player = Player(
            x=player_start_full_pos[0],
            y=player_start_full_pos[1],
            current_floor_id=player_start_full_pos[2],
            health=20,
        )
        self.game_state = GameState.PLAYING
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

        self._initialize_monster_ai()
        self._update_fog_of_war_visibility()
        self.world_maps[self.player.current_floor_id].place_player(
            self.player, self.player.x, self.player.y
        )

    def _initialize_monster_ai(self):
        for floor_id, world_map in self.world_maps.items():
            for monster in world_map.get_monsters():
                monster.ai = MonsterAILogic(
                    monster=monster,
                    player=self.player,
                    world_map=world_map,
                    random_generator=self.random,
                )

    def _handle_monster_actions(self):
        current_map = self.world_maps.get(self.player.current_floor_id)
        if not current_map:
            return

        for monster in current_map.get_monsters():
            if monster.health > 0 and monster.ai:
                monster.move_energy += monster.move_speed
                if monster.move_energy >= 10:
                    action = monster.ai.get_next_action()
                    if action:
                        is_move_action = action[0] == "move"
                        if is_move_action:
                            monster.move_energy -= 10
                        self.command_processor.process_monster_command(
                            action,
                            monster,
                            self.player,
                            self.world_maps,
                            self.message_log,
                        )

    def _update_fog_of_war_visibility(self) -> None:
        player_x, player_y = self.player.x, self.player.y
        current_floor_id = self.player.current_floor_id

        current_real_map = self.world_maps.get(current_floor_id)
        current_visible_map = self.visible_maps.get(current_floor_id)

        if not current_real_map or not current_visible_map:
            self.message_log.add_message(
                f"Error: Invalid floor ID {current_floor_id} for visibility."
            )
            return

        # At the beginning of the update, clear all monster visibility on the
        # visible map. This ensures that monsters that move out of sight are no
        # longer drawn.
        for y in range(current_visible_map.height):
            for x in range(current_visible_map.width):
                tile = current_visible_map.get_tile(x, y)
                if tile:
                    tile.monster = None

        # This is for revealing the map, items, and portals
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
                        # Don't update monster here, handle it separately
                        visible_tile.item = real_tile.item
                        visible_tile.is_portal = real_tile.is_portal
                        visible_tile.portal_to_floor_id = real_tile.portal_to_floor_id
                        visible_tile.is_explored = True

        # Now, specifically handle monster visibility on currently visible tiles.
        for y in range(player_y - 1, player_y + 2):
            for x in range(player_x - 1, player_x + 2):
                if not (
                    0 <= x < current_real_map.width and 0 <= y < current_real_map.height
                ):
                    continue

                real_tile = current_real_map.get_tile(x, y)
                if real_tile and real_tile.monster:
                    visible_tile = current_visible_map.get_tile(x, y)
                    if visible_tile:
                        visible_tile.monster = real_tile.monster

    def run(self):
        if self.debug_mode:
            print("--- Starting Game in Debug Mode ---")
            print(f"\nPlayer initial position: ({self.player.x}, {self.player.y})")
            print(f"Player initial health: {self.player.health}")
            print(f"Winning position: {self.winning_full_pos}")
            self._print_full_map_debug()

        try:
            start_time = time.time()
            timeout_seconds = 30
            ai_state = None

            self._update_fog_of_war_visibility()
            if not self.debug_mode:
                self._render()

            while self.game_state != GameState.QUIT:
                if self.game_state == GameState.PLAYING:
                    if self.debug_mode and time.time() - start_time > timeout_seconds:
                        print("--- Debug Mode Timeout ---")
                        self.game_state = GameState.GAME_OVER
                        continue

                    self._handle_invisibility()
                    self._update_fog_of_war_visibility()

                    parsed_command_output = self._get_next_command()
                    if parsed_command_output:
                        self._process_command(parsed_command_output)
                        ai_state = (
                            self.ai_logic.state.__class__.__name__
                            if self.ai_active and self.ai_logic
                            else None
                        )

                    if self.game_state == GameState.PLAYING and not self.debug_mode:
                        self._render(ai_state=ai_state)
                elif self.game_state == GameState.GAME_OVER:
                    if self.debug_mode:
                        break
                    else:
                        # In non-debug mode, wait for input to exit
                        self.input_handler.handle_input_and_get_command()
                        self.game_state = GameState.QUIT
                        continue

            if self.debug_mode:
                self._render_debug_end_screen(ai_state=ai_state)
            elif self.game_state == GameState.GAME_OVER:
                self._render(ai_state=ai_state)
                curses.napms(2000)

        finally:
            if not self.debug_mode:
                self.renderer.cleanup_curses()

    def _get_next_command(self):
        if self.ai_active and self.ai_logic:
            if self.ai_sleep_duration > 0 and not self.debug_mode:
                time.sleep(self.ai_sleep_duration)
            return self.ai_logic.get_next_action()
        elif not self.debug_mode:
            return self.input_handler.handle_input_and_get_command()
        else:
            self.game_state = GameState.GAME_OVER
            return None

    def _process_command(self, parsed_command_output):
        if self.game_state != GameState.PLAYING:
            self.message_log.add_message("The game is over.")
            return

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

        if results.get("game_over", False):
            self.game_state = GameState.GAME_OVER

        if self.game_state == GameState.PLAYING:
            self._handle_monster_actions()
            self._update_fog_of_war_visibility()

        floor_after_command = self.player.current_floor_id
        if (
            self.ai_active
            and self.ai_logic
            and floor_before_command != floor_after_command
        ):
            self.ai_logic.current_path = None
            self.message_log.add_message("AI: Floor changed, clearing path.")

    def _render(self, ai_state=None):
        current_visible_map = self.visible_maps.get(self.player.current_floor_id)
        if not current_visible_map:
            current_visible_map = WorldMap(
                self.renderer.map_width, self.renderer.map_height
            )

        ai_path = None
        if self.ai_active and self.ai_logic:
            ai_path = self.ai_logic.current_path

        self.renderer.render_all(
            player_x=self.player.x,
            player_y=self.player.y,
            player_health=self.player.health,
            world_map_to_render=current_visible_map,
            input_mode=self.input_handler.get_input_mode(),
            current_command_buffer=self.input_handler.get_command_buffer(),
            message_log=self.message_log,
            debug_render_to_list=self.debug_mode,
            ai_path=ai_path,
            current_floor_id=self.player.current_floor_id,
            ai_state=ai_state,
        )

    def _render_debug_end_screen(self, ai_state=None):
        print("\n--- Game Over ---")
        final_map_render = self.renderer.render_all(
            player_x=self.player.x,
            player_y=self.player.y,
            player_health=self.player.health,
            world_map_to_render=self.visible_maps.get(
                self.player.current_floor_id, self.world_maps.get(0)
            ),
            input_mode="",
            current_command_buffer="",
            message_log=self.message_log,
            debug_render_to_list=True,
            ai_path=self.ai_logic.current_path if self.ai_logic else None,
            current_floor_id=self.player.current_floor_id,
            ai_state=ai_state,
        )
        if final_map_render:
            for row in final_map_render:
                print(row)

        print("\n--- Final Messages ---")
        for msg in self.message_log.messages:
            print(msg)

        print("\n--- Debug Mode Finished ---")

    def _handle_item_use(self, item):
        item_type = item.properties.get("type")
        if item_type == "teleport":
            self._teleport_player()
        elif item_type == "damage":
            self._handle_damage_item(item)

    def _teleport_player(self):
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
        self.message_log.add_message(f"You can throw the {item.name}.")

    def _handle_invisibility(self):
        if self.player.invisibility_turns > 0:
            self.player.invisibility_turns -= 1
            if self.player.invisibility_turns == 0:
                self.message_log.add_message("You are no longer invisible.")

    def _print_full_map_debug(self):
        print("\n--- World Map Layout ---")
        for floor_id, world_map in sorted(self.world_maps.items()):
            print(f"\n--- Floor {floor_id} ---")
            map_render = world_map.get_map_as_string(self.renderer, self.message_log)
            if map_render:
                for row in map_render:
                    print(row)

            portal_info = []
            for y in range(world_map.height):
                for x in range(world_map.width):
                    tile = world_map.get_tile(x, y)
                    if tile and tile.is_portal:
                        portal_info.append(
                            f"Portal at ({x}, {y}) -> Floor {tile.portal_to_floor_id}"
                        )
            if portal_info:
                print("Portals:")
                for info in portal_info:
                    print(f"- {info}")

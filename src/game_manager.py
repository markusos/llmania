from __future__ import annotations

import curses
import logging
import time
from typing import TYPE_CHECKING

from src.command_processor import CommandProcessor
from src.game_state import GameState
from src.input_handler import InputHandler
from src.message_log import MessageLog
from src.renderer import Renderer

if TYPE_CHECKING:
    from src.ai_logic import AILogic
    from src.player import Player
    from src.world_map import WorldMap
logger = logging.getLogger(__name__)


class GameManager:
    """Manages the game state, player actions, and game loop.
    This class is responsible for orchestrating the main game flow, including
    handling player and monster actions, processing commands, and determining
    the game state.
    Args:
        player (Player): The player character.
        world_maps (dict[int, WorldMap]): A dictionary of all world maps.
        message_log (MessageLog): The message log for displaying game messages.
        renderer (Renderer): The renderer for displaying the game.
        input_handler (InputHandler): The input handler for processing player input.
        command_processor (CommandProcessor): The command processor for executing
                                              commands.
        ai_logic (AILogic | None): The AI logic for controlling the player.
        debug_mode (bool): A flag indicating whether the game is in debug mode.
    """

    def __init__(
        self,
        player: Player,
        world_maps: dict[int, WorldMap],
        visible_maps: dict[int, WorldMap],
        message_log: MessageLog,
        renderer: Renderer,
        input_handler: InputHandler,
        command_processor: CommandProcessor,
        ai_logic: AILogic | None = None,
        debug_mode: bool = False,
    ):
        self.player = player
        self.world_maps = world_maps
        self.visible_maps = visible_maps
        self.message_log = message_log
        self.renderer = renderer
        self.input_handler = input_handler
        self.command_processor = command_processor
        self.ai_logic = ai_logic
        self.debug_mode = debug_mode
        self.game_state = GameState.PLAYING

    def run(self, fog_of_war) -> None:
        """
        Runs the main game loop.
        """
        start_time = time.time()
        timeout_seconds = 30
        ai_state = None

        fog_of_war.update_visibility()
        if not self.debug_mode:
            self._render()

        while self.game_state == GameState.PLAYING:
            if self.debug_mode and time.time() - start_time > timeout_seconds:
                print("--- Debug Mode Timeout ---")
                self.game_state = GameState.GAME_OVER
                break

            self._handle_invisibility()
            fog_of_war.update_visibility()

            parsed_command_output = self._get_next_command()
            if parsed_command_output == "NO_COMMAND":
                self.game_state = GameState.QUIT
                break

            if parsed_command_output:
                self._process_command(parsed_command_output)
                ai_state = (
                    self.ai_logic.state.__class__.__name__ if self.ai_logic else None
                )

            if self.game_state == GameState.PLAYING and not self.debug_mode:
                self._render(ai_state=ai_state)

            if self.player.health <= 0:
                self.game_state = GameState.GAME_OVER

    def _get_next_command(self):
        if self.ai_logic:
            return self.ai_logic.get_next_action()
        elif not self.debug_mode:
            return self.input_handler.handle_input_and_get_command()
        else:
            # In debug mode, if not AI-controlled, we assume commands are fed in
            # and we should not block on input. If no more commands, exit.
            if hasattr(self, "_debug_commands") and self._debug_commands:
                return self._debug_commands.pop(0)
            return "NO_COMMAND"

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
            (0, 0, -1),  # winning_full_pos
            game_engine=self,
        )
        if "used_item" in results:
            self._handle_item_use(results["used_item"])

        if results.get("game_over", False):
            self.game_state = GameState.GAME_OVER

        if self.game_state == GameState.PLAYING:
            self._handle_monster_actions()
            # self._update_fog_of_war_visibility()

        floor_after_command = self.player.current_floor_id
        if self.ai_logic and floor_before_command != floor_after_command:
            self.ai_logic.current_path = None
            self.message_log.add_message("AI: Floor changed, clearing path.")

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

    def _handle_game_over(self):
        if self.game_state == GameState.GAME_OVER:
            if self.player.health <= 0:
                self.message_log.add_message("You have been defeated. Game Over.")

            ai_state = self.ai_logic.state.__class__.__name__ if self.ai_logic else None

            if self.debug_mode:
                self._render_debug_end_screen(ai_state=ai_state)
            else:
                self._render(ai_state=ai_state)
                curses.napms(2000)
                self.input_handler.handle_input_and_get_command()
                self.game_state = GameState.QUIT

        elif self.game_state == GameState.QUIT and self.debug_mode:
            ai_state = self.ai_logic.state.__class__.__name__ if self.ai_logic else None
            self._render_debug_end_screen(ai_state=ai_state)

    def _render(self, ai_state=None):
        current_visible_map = self.visible_maps.get(self.player.current_floor_id)
        if not current_visible_map:
            current_visible_map = WorldMap(
                self.renderer.map_width, self.renderer.map_height
            )

        self.renderer.render_all(
            player_x=self.player.x,
            player_y=self.player.y,
            player_health=self.player.health,
            world_map_to_render=current_visible_map,
            input_mode=self.input_handler.current_mode,
            current_command_buffer=self.input_handler.command_buffer,
            message_log=self.message_log,
            current_floor_id=self.player.current_floor_id,
            ai_path=self.ai_logic.current_path if self.ai_logic else None,
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
            # self._update_fog_of_war_visibility()

    def _handle_damage_item(self, item):
        self.message_log.add_message(f"You can throw the {item.name}.")

    def _handle_invisibility(self):
        if self.player.invisibility_turns > 0:
            self.player.invisibility_turns -= 1
            if self.player.invisibility_turns == 0:
                self.message_log.add_message("You are no longer invisible.")

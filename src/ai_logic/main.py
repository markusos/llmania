from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder

from .explorer import Explorer
from .states.attacking_state import AttackingState
from .states.exploring_state import ExploringState
from .states.looting_state import LootingState
from .states.survival_state import SurvivalState
from .target_finder import TargetFinder

if TYPE_CHECKING:
    from random import Random

    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap

    from .states import AIState


class AILogic:
    def _get_state(self, state_name: str) -> "AIState":
        if state_name == "ExploringState":
            return ExploringState(self)
        elif state_name == "AttackingState":
            return AttackingState(self)
        elif state_name == "LootingState":
            return LootingState(self)
        elif state_name == "SurvivalState":
            return SurvivalState(self)
        else:
            raise ValueError(f"Unknown state name: {state_name}")

    """
    Handles the decision-making for AI-controlled characters, primarily the player
    when AI mode is active.
    """

    def __init__(
        self,
        player: "Player",
        real_world_maps: Dict[int, "WorldMap"],
        ai_visible_maps: Dict[int, "WorldMap"],
        message_log: "MessageLog",
        random_generator: "Random",
        verbose: int = 0,
    ):
        self.player = player
        self.real_world_maps = real_world_maps
        self.ai_visible_maps = ai_visible_maps
        self.message_log = message_log
        self.random = random_generator
        self.verbose = verbose
        self.path_finder = PathFinder()
        self.current_path: Optional[List[Tuple[int, int, int]]] = None
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None
        self.target_finder = TargetFinder(self.player, self.ai_visible_maps)
        self.explorer = Explorer(self.player, self.ai_visible_maps)
        self.state: "AIState" = ExploringState(self)
        self.last_player_floor_id = player.current_floor_id
        self.last_player_pos = (player.x, player.y)
        self.player_pos_history = []
        self.command_history: List[Optional[Tuple[str, Optional[str]]]] = []

    def _is_in_loop(self, lookback: int = 4) -> bool:
        if len(self.command_history) < lookback:
            return False
        last_commands = self.command_history[-lookback:]
        if len(set(last_commands)) <= 2:
            return True
        return False

    def _get_adjacent_monsters(self) -> List["Monster"]:
        adjacent_monsters: List["Monster"] = []
        current_floor_id = self.player.current_floor_id
        current_ai_map = self.ai_visible_maps.get(current_floor_id)
        if not current_ai_map:
            return []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_x, check_y = self.player.x + dx, self.player.y + dy
            tile = current_ai_map.get_tile(check_x, check_y)
            if tile and tile.is_explored and tile.monster:
                adjacent_monsters.append(tile.monster)
        return adjacent_monsters

    def _coordinates_to_move_command(
        self, start_pos_xy: Tuple[int, int], end_pos_xy: Tuple[int, int]
    ) -> Optional[Tuple[str, str]]:
        dx = end_pos_xy[0] - start_pos_xy[0]
        dy = end_pos_xy[1] - start_pos_xy[1]
        if dx == 0 and dy == -1:
            return ("move", "north")
        if dx == 0 and dy == 1:
            return ("move", "south")
        if dx == -1 and dy == 0:
            return ("move", "west")
        if dx == 1 and dy == 0:
            return ("move", "east")
        return None

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        action = self._get_next_action_logic()
        self.command_history.append(action)
        if len(self.command_history) > 10:
            self.command_history.pop(0)
        if self.verbose > 0:
            if action:
                print(f"AI Action: {action[0]} {action[1] if action[1] else ''}")
            else:
                print("AI Action: None")
        return action

    def _get_next_action_logic(self) -> Optional[Tuple[str, Optional[str]]]:
        if self.player.current_floor_id != self.last_player_floor_id:
            prev_map = self.ai_visible_maps.get(self.last_player_floor_id)
            if prev_map:
                prev_tile = prev_map.get_tile(
                    self.last_player_pos[0], self.last_player_pos[1]
                )
                if prev_tile and prev_tile.is_portal:
                    self.explorer.mark_portal_as_visited(
                        self.last_player_pos[0],
                        self.last_player_pos[1],
                        self.last_player_floor_id,
                    )
                    if self.verbose > 0:
                        print(
                            "AI: Portal at "
                            f"({self.last_player_pos[0]},{self.last_player_pos[1]}) "
                            f"on floor {self.last_player_floor_id} marked as visited."
                        )

        self.last_player_floor_id = self.player.current_floor_id
        self.last_player_pos = (self.player.x, self.player.y)

        # Stuck detection
        self.player_pos_history.append(self.last_player_pos)
        if len(self.player_pos_history) > 4:
            self.player_pos_history.pop(0)
            if len(set(self.player_pos_history)) <= 2:
                self.current_path = None
                self.player_pos_history = []

        # Delegate action to the current state
        next_state_name = self.state.handle_transitions()
        if next_state_name != self.state.__class__.__name__:
            self.state = self._get_state(next_state_name)
        return self.state.get_next_action()

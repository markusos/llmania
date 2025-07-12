from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder

from .explorer import Explorer
from .states import AttackingState, ExploringState, LootingState
from .target_finder import TargetFinder

if TYPE_CHECKING:
    from random import Random

    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap

    from .states import AIState


class AILogic:
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
        if self.verbose > 0:
            if action:
                print(f"AI Action: {action[0]} {action[1] if action[1] else ''}")
            else:
                print("AI Action: None")
        return action

    def _get_next_action_logic(self) -> Optional[Tuple[str, Optional[str]]]:
        # Update state based on observations
        self._update_state()

        # Delegate action to the current state
        return self.state.get_next_action()

    def _update_state(self):
        # Check for adjacent monsters
        if self._get_adjacent_monsters():
            if not isinstance(self.state, AttackingState):
                self.state = AttackingState(self)
            return

        # Check for items on the current tile
        current_ai_map = self.ai_visible_maps.get(self.player.current_floor_id)
        if current_ai_map:
            current_tile = current_ai_map.get_tile(self.player.x, self.player.y)
            if current_tile and current_tile.item:
                if not isinstance(self.state, LootingState):
                    self.state = LootingState(self)
                return

        # Default to exploring
        if not isinstance(self.state, ExploringState):
            self.state = ExploringState(self)

    def _follow_path(self) -> Optional[Tuple[str, Optional[str]]]:
        if self.current_path:
            current_pos_xyz = (
                self.player.x,
                self.player.y,
                self.player.current_floor_id,
            )
            if self.current_path[0] == current_pos_xyz:
                self.current_path.pop(0)
            if not self.current_path:
                self.current_path = None
                return None

            next_step_xyz = self.current_path[0]
            move_command = self._coordinates_to_move_command(
                (current_pos_xyz[0], current_pos_xyz[1]),
                (next_step_xyz[0], next_step_xyz[1]),
            )
            if move_command:
                log_msg = (
                    f"AI: Following path. Moving {move_command[1]} to "
                    f"({next_step_xyz[0]},{next_step_xyz[1]}) on floor "
                    f"{next_step_xyz[2]}."
                )
                self.message_log.add_message(log_msg)
                self.last_move_command = move_command
                return move_command
        return None

    def _explore_randomly(self) -> Optional[Tuple[str, Optional[str]]]:
        current_ai_map = self.ai_visible_maps.get(self.player.current_floor_id)
        if not current_ai_map:
            return None

        possible_moves = []
        for direction, (dx, dy) in [
            ("north", (0, -1)),
            ("south", (0, 1)),
            ("west", (-1, 0)),
            ("east", (1, 0)),
        ]:
            check_x, check_y = self.player.x + dx, self.player.y + dy
            if current_ai_map.is_valid_move(check_x, check_y):
                possible_moves.append(("move", direction))

        if possible_moves:
            return self.random.choice(possible_moves)
        return ("look", None)

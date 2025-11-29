from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from src.ai_logic.states import common_actions

if TYPE_CHECKING:
    from src.ai_logic.main import AILogic


class AIState:
    def __init__(self, ai_logic: "AILogic"):
        self.ai_logic = ai_logic

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        raise NotImplementedError

    def handle_transitions(self) -> str:
        # Default behavior: no transition
        return self.__class__.__name__

    def _use_item(self, item_type: str) -> Optional[Tuple[str, str]]:
        return common_actions.use_item(self.ai_logic, item_type)

    def _equip_better_weapon(self) -> Optional[Tuple[str, str]]:
        return common_actions.equip_better_weapon(self.ai_logic)

    def _equip_beneficial_items(self) -> Optional[Tuple[str, str]]:
        """Equip armor and better weapons automatically."""
        return common_actions.equip_beneficial_items(self.ai_logic)

    def _pickup_item(self) -> Optional[Tuple[str, str]]:
        return common_actions.pickup_item(self.ai_logic)

    def _path_to_best_target(
        self,
        target_finder_func: Callable[
            [Tuple[int, int], int], List[Tuple[int, int, int, str, int]]
        ],
        sort_key_func: Optional[
            Callable[[Tuple[int, int, int, str, int]], Tuple[int, int]]
        ] = None,
    ) -> Optional[Tuple[str, Optional[str]]]:
        return common_actions.path_to_best_target(
            self.ai_logic, target_finder_func, sort_key_func
        )

    def _follow_path(self) -> Optional[Tuple[str, Optional[str]]]:
        if self.ai_logic._is_in_loop():
            self.ai_logic._break_loop()
            return None

        if self.ai_logic.current_path:
            current_pos_xyz = (
                self.ai_logic.player_view.x,
                self.ai_logic.player_view.y,
                self.ai_logic.player_view.current_floor_id,
            )
            if self.ai_logic.current_path[0] == current_pos_xyz:
                self.ai_logic.current_path.pop(0)
            if not self.ai_logic.current_path:
                self.ai_logic.current_path = None
                return None

            next_step_xyz = self.ai_logic.current_path[0]
            move_command = self.ai_logic._coordinates_to_move_command(
                (current_pos_xyz[0], current_pos_xyz[1]),
                (next_step_xyz[0], next_step_xyz[1]),
            )
            if move_command:
                log_msg = (
                    f"AI: Following path. Moving {move_command[1]} to "
                    f"({next_step_xyz[0]},{next_step_xyz[1]}) on floor "
                    f"{next_step_xyz[2]}."
                )
                self.ai_logic.message_log.add_message(log_msg)
                self.ai_logic.last_move_command = move_command
                return move_command
        return None

    def _explore_randomly(
        self, break_loop: bool = False
    ) -> Optional[Tuple[str, Optional[str]]]:
        if not break_loop and self.ai_logic._is_in_loop():
            self.ai_logic._break_loop()
            return None

        current_ai_map = self.ai_logic.ai_visible_maps.get(
            self.ai_logic.player_view.current_floor_id
        )
        if not current_ai_map:
            return None

        possible_moves = []
        monster_moves = []  # Track moves that would walk into monsters
        for direction, (dx, dy) in [
            ("north", (0, -1)),
            ("south", (0, 1)),
            ("west", (-1, 0)),
            ("east", (1, 0)),
        ]:
            player_view = self.ai_logic.player_view
            check_x, check_y = player_view.x + dx, player_view.y + dy
            if current_ai_map.is_valid_move(check_x, check_y):
                tile = current_ai_map.get_tile(check_x, check_y)
                # Avoid walking into monsters during random exploration
                if tile and tile.monster:
                    monster_moves.append(("move", direction))
                else:
                    possible_moves.append(("move", direction))

        # If no safe moves, allow monster moves as last resort (cornered)
        if not possible_moves:
            possible_moves = monster_moves

        if not possible_moves:
            return ("look", None)

        # Try to avoid going back to where we just came from
        opposite_moves = {
            ("move", "north"): ("move", "south"),
            ("move", "south"): ("move", "north"),
            ("move", "east"): ("move", "west"),
            ("move", "west"): ("move", "east"),
        }
        if len(possible_moves) > 1:
            last_cmd = self.ai_logic.last_move_command
            if last_cmd:
                # Get the opposite of the last move (which would take us back)
                opposite = opposite_moves.get(last_cmd)
                if opposite and opposite in possible_moves:
                    # Filter out the opposite move to avoid oscillation
                    filtered_moves = [m for m in possible_moves if m != opposite]
                    if filtered_moves:
                        return self.ai_logic.random.choice(filtered_moves)

        # Fallback to choosing any possible move if no other options
        return self.ai_logic.random.choice(possible_moves)

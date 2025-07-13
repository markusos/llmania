from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

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

    def _follow_path(self) -> Optional[Tuple[str, Optional[str]]]:
        if self.ai_logic.current_path:
            current_pos_xyz = (
                self.ai_logic.player.x,
                self.ai_logic.player.y,
                self.ai_logic.player.current_floor_id,
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

    def _explore_randomly(self) -> Optional[Tuple[str, Optional[str]]]:
        current_ai_map = self.ai_logic.ai_visible_maps.get(
            self.ai_logic.player.current_floor_id
        )
        if not current_ai_map:
            return None

        possible_moves = []
        for direction, (dx, dy) in [
            ("north", (0, -1)),
            ("south", (0, 1)),
            ("west", (-1, 0)),
            ("east", (1, 0)),
        ]:
            check_x, check_y = self.ai_logic.player.x + dx, self.ai_logic.player.y + dy
            if current_ai_map.is_valid_move(check_x, check_y):
                possible_moves.append(("move", direction))

        if possible_moves:
            return self.ai_logic.random.choice(possible_moves)
        return ("look", None)

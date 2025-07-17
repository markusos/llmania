from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_state import AIState

if TYPE_CHECKING:
    from src.monster_ai.main import MonsterAILogic


class AttackingState(AIState):
    def __init__(self, ai_logic: "MonsterAILogic"):
        super().__init__(ai_logic)

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        # If player is in attack range, attack
        if self.ai_logic.is_player_in_attack_range():
            return "attack", None

        # If player is in line of sight but not in attack range, move towards player
        if self.ai_logic.is_player_in_line_of_sight():
            return self.ai_logic.move_towards_player()

        # If player is not in line of sight, do nothing
        return None

    def handle_transitions(self) -> str:
        # If player is not in line of sight, switch to idle state
        if not self.ai_logic.is_player_in_line_of_sight():
            return "IdleState"
        return "AttackingState"

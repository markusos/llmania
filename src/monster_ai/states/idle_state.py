from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_state import AIState

if TYPE_CHECKING:
    from src.monster_ai.main import MonsterAILogic


class IdleState(AIState):
    def __init__(self, ai_logic: "MonsterAILogic"):
        super().__init__(ai_logic)

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        # Monsters in idle state do nothing
        return None

    def handle_transitions(self) -> str:
        # If player is in line of sight, switch to attacking state
        if self.ai_logic.is_player_in_line_of_sight():
            return "AttackingState"
        return "IdleState"

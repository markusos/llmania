from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_state import AIState

if TYPE_CHECKING:
    pass


class AttackingState(AIState):
    def handle_transitions(self) -> "AIState":
        from .exploring_state import ExploringState
        from .survival_state import SurvivalState

        player = self.ai_logic.player
        if player.health <= player.max_health / 2:
            return SurvivalState(self.ai_logic)
        if not self.ai_logic._get_adjacent_monsters():
            return ExploringState(self.ai_logic)
        return self

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        adjacent_monsters = self.ai_logic._get_adjacent_monsters()
        if adjacent_monsters:
            monster_to_attack = self.ai_logic.random.choice(adjacent_monsters)
            self.ai_logic.message_log.add_message(
                f"AI: Attacking adjacent {monster_to_attack.name}."
            )
            self.ai_logic.current_path = None
            return ("attack", monster_to_attack.name)
        return None

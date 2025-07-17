from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from src.monster_ai.main import MonsterAILogic


class AIState:
    def __init__(self, ai_logic: "MonsterAILogic"):
        self.ai_logic = ai_logic

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        raise NotImplementedError

    def handle_transitions(self) -> str:
        # Default behavior: no transition
        return self.__class__.__name__

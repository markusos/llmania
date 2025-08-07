from __future__ import annotations

from typing import TYPE_CHECKING

from .base_effect import Effect

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class StatBuffEffect(Effect):
    def __init__(self, stat: str, bonus: int, duration: int):
        self.stat = stat
        self.bonus = bonus
        self.duration = duration

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        # The logic for applying and tracking stat buffs will need to be
        # implemented in the Player class.
        # For now, this is a placeholder.
        return (
            f"You feel a surge of power! Your {self.stat} is "
            f"increased by {self.bonus} for {self.duration} turns."
        )

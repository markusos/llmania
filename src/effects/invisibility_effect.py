from __future__ import annotations

from typing import TYPE_CHECKING

from .base_effect import Effect

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class InvisibilityEffect(Effect):
    def __init__(self, duration: int):
        self.duration = duration

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        player.invisibility_turns += self.duration
        return f"You drink the potion and become invisible for {self.duration} turns."

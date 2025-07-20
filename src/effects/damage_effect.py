from __future__ import annotations

from typing import TYPE_CHECKING

from .base_effect import Effect

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class DamageEffect(Effect):
    def __init__(self, damage_amount: int):
        self.damage_amount = damage_amount

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        # For now, this is just a placeholder.
        # We can implement targeting later.
        return "The item crackles with power, ready to be thrown."

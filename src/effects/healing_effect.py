from __future__ import annotations

from typing import TYPE_CHECKING

from .base_effect import Effect

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class HealingEffect(Effect):
    def __init__(self, heal_amount: int):
        self.heal_amount = heal_amount

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        healed_amount = player.heal(self.heal_amount)
        if healed_amount > 0:
            return f"You feel a warm glow and recover {healed_amount} HP."
        return "You are already at full health."

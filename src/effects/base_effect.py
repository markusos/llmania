from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class Effect:
    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        raise NotImplementedError()

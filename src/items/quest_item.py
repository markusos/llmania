from __future__ import annotations

from typing import TYPE_CHECKING

from src.items.item import Item

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class QuestItem(Item):
    """
    An item that is part of a quest.
    """

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        return "This is a quest item and cannot be used directly."

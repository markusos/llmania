from __future__ import annotations

from typing import TYPE_CHECKING

from src.items.item import Item

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class ReadableItem(Item):
    """
    An item that can be read.
    """

    def __init__(self, name: str, description: str, properties: dict, text: str):
        super().__init__(name, description, properties)
        self.text = text

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        return self.text

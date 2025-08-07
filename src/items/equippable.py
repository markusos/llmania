from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.items.item import Item

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class EquippableItem(Item):
    """
    Represents an equippable item in the game.
    """

    def __init__(self, name: str, description: str, properties: dict):
        """
        Initializes an Equippable instance.
        """
        super().__init__(name, description, properties)
        self.slot: Optional[str] = properties.get("slot")
        self.attack_bonus: int = properties.get("attack_bonus", 0)
        self.defense_bonus: int = properties.get("defense_bonus", 0)
        self.speed_bonus: int = properties.get("speed_bonus", 0)
        self.max_health_bonus: int = properties.get("max_health_bonus", 0)

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        """
        Equips or unequips the item.
        """
        return player.toggle_equip(self)

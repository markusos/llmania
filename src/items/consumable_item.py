from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.items.item import Item

if TYPE_CHECKING:
    from src.effects.base_effect import Effect
    from src.game_engine import GameEngine
    from src.player import Player


class ConsumableItem(Item):
    """
    An item that is consumed on use.
    """

    def __init__(
        self,
        name: str,
        description: str,
        properties: dict,
        effects: List["Effect"],
    ):
        super().__init__(name, description, properties)
        self.effects = effects

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        """
        Applies the item's effects to the player and removes it from the
        inventory.
        """
        messages = []
        for effect in self.effects:
            messages.append(effect.apply(player, game_engine))
        player.inventory.remove_item(self)
        return " ".join(messages)

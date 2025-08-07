from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.items.item import Item

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class ContainerItem(Item):
    """
    An item that can contain other items.
    """

    def __init__(
        self,
        name: str,
        description: str,
        properties: dict,
        capacity: int,
        contained_items: List[Item],
    ):
        super().__init__(name, description, properties)
        self.capacity = capacity
        self.contained_items = contained_items

    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        if len(self.contained_items) == 0:
            return f"The {self.name} is empty."
        else:
            # For now, let's just list the items.
            # In the future, we could open a container view.
            item_names = ", ".join([item.name for item in self.contained_items])
            return f"The {self.name} contains: {item_names}"

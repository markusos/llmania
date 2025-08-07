from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.items.item import Item


class Inventory:
    """
    Manages a collection of items.
    """

    def __init__(self):
        self.items: List[Item] = []

    def add_item(self, item: Item):
        """
        Adds an item to the inventory.
        """
        self.items.append(item)

    def remove_item(self, item: Item):
        """
        Removes an item from the inventory.
        """
        self.items.remove(item)

    def find_item(self, item_name: str) -> Optional[Item]:
        """
        Finds an item in the inventory by name.
        """
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item
        return None

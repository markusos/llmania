import json
import random
from typing import Optional

from src.equippable import Equippable
from src.item import Item


class ItemFactory:
    """
    Factory for creating items from a data file.
    """

    def __init__(self, item_data_path: str):
        """
        Initializes the ItemFactory.

        Args:
            item_data_path: The path to the JSON file containing item data.
        """
        with open(item_data_path, "r") as f:
            self.item_data = json.load(f)

    def create_item(self, item_id: str) -> Optional[Item]:
        """
        Creates an item instance based on the given item ID.

        Args:
            item_id: The ID of the item to create.

        Returns:
            An Item instance, or None if the item ID is not found.
        """
        item_info = self.item_data.get(item_id)
        if not item_info:
            return None

        properties = item_info.get("properties", {})
        if properties.get("type") == "weapon":
            return Equippable(
                name=item_info["name"],
                description=item_info["description"],
                properties=properties,
            )
        else:
            return Item(
                name=item_info["name"],
                description=item_info["description"],
                properties=properties,
            )

    def create_random_item(self) -> Optional[Item]:
        """
        Creates a random item from the available item data based on rarity.

        Returns:
            A random Item instance, or None if there is no item data.
        """
        if not self.item_data:
            return None

        rarity_sum = sum(item.get("rarity", 0) for item in self.item_data.values())
        if rarity_sum == 0:
            return None

        roll = random.randint(1, rarity_sum)
        current_sum = 0
        for item_id, item_info in self.item_data.items():
            current_sum += item_info.get("rarity", 0)
            if roll <= current_sum:
                return self.create_item(item_id)

        return None

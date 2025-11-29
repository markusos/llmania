import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.effects import (
    DamageEffect,
    Effect,
    HealingEffect,
    InvisibilityEffect,
    StatBuffEffect,
    TeleportEffect,
)
from src.items import (
    ConsumableItem,
    ContainerItem,
    EquippableItem,
    Item,
    QuestItem,
    ReadableItem,
)

if TYPE_CHECKING:
    from random import Random


class ItemFactory:
    """
    Factory for creating items from a data file.
    """

    def __init__(self, item_data_path: str):
        """
        Initializes the ItemFactory.
        """
        with open(item_data_path, "r") as f:
            self.item_data = json.load(f)

    def create_item(self, item_id: str) -> Optional[Item]:
        """
        Creates an item instance based on the given item ID.
        """
        item_info = self.item_data.get(item_id)
        if not item_info:
            return None

        properties = item_info.get("properties", {})
        item_type = properties.get("type")

        if item_type == "equippable":
            return EquippableItem(
                name=item_info["name"],
                description=item_info["description"],
                properties=properties,
            )
        elif item_type == "consumable":
            effects = self._create_effects(properties.get("effects", []))
            return ConsumableItem(
                name=item_info["name"],
                description=item_info["description"],
                properties=properties,
                effects=effects,
            )
        elif item_type == "quest":
            return QuestItem(
                name=item_info["name"],
                description=item_info["description"],
                properties=properties,
            )
        elif item_type == "readable":
            return ReadableItem(
                name=item_info["name"],
                description=item_info["description"],
                properties=properties,
                text=properties.get("text", ""),
            )
        elif item_type == "container":
            contained_items = [
                self.create_item(item) for item in properties.get("contained_items", [])
            ]
            return ContainerItem(
                name=item_info["name"],
                description=item_info["description"],
                properties=properties,
                capacity=properties.get("capacity", 0),
                contained_items=[item for item in contained_items if item is not None],
            )
        else:
            # For backward compatibility, we can try to guess the type
            if "slot" in properties:
                return EquippableItem(
                    name=item_info["name"],
                    description=item_info["description"],
                    properties=properties,
                )
            else:
                # Default to a generic item or handle as an error
                return None

    def _create_effects(self, effects_data: List[Dict[str, Any]]) -> List[Effect]:
        effects = []
        for data in effects_data:
            effect_type = data.get("type")
            if effect_type == "healing":
                effects.append(HealingEffect(data.get("amount", 0)))
            elif effect_type == "damage":
                effects.append(DamageEffect(data.get("damage", 0)))
            elif effect_type == "teleport":
                effects.append(TeleportEffect())
            elif effect_type == "invisibility":
                effects.append(InvisibilityEffect(data.get("duration", 0)))
            elif effect_type == "stat_buff":
                effects.append(
                    StatBuffEffect(
                        data.get("stat", ""),
                        data.get("bonus", 0),
                        data.get("duration", 0),
                    )
                )
        return effects

    def create_random_item(self, random_generator: "Random") -> Optional[Item]:
        """
        Creates a random item from the available item data based on rarity.
        """
        if not self.item_data:
            return None

        rarity_sum = sum(item.get("rarity", 0) for item in self.item_data.values())
        if rarity_sum == 0:
            # Fallback to choosing any item if rarity is not defined
            item_id = random_generator.choice(list(self.item_data.keys()))
            return self.create_item(item_id)

        roll = random_generator.randint(1, rarity_sum)
        current_sum = 0
        for item_id, item_info in self.item_data.items():
            current_sum += item_info.get("rarity", 0)
            if roll <= current_sum:
                return self.create_item(item_id)

        return None

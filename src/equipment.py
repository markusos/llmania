from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from src.items.equippable import EquippableItem


class Equipment:
    """
    Manages the player's equipped items.
    """

    def __init__(self):
        self.slots: Dict[str, Optional[EquippableItem]] = {
            "head": None,
            "chest": None,
            "legs": None,
            "main_hand": None,
            "off_hand": None,
            "ring": None,
            "amulet": None,
            "boots": None,
        }

    def equip(self, item: EquippableItem, slot: str) -> Optional[EquippableItem]:
        """
        Equips an item to a slot, returning the previously equipped item if any.
        """
        if slot not in self.slots:
            return None  # Or raise an error

        previous_item = self.slots[slot]
        self.slots[slot] = item
        return previous_item

    def unequip(self, slot: str) -> Optional[EquippableItem]:
        """
        Unequips an item from a slot, returning the item that was unequipped.
        """
        if slot not in self.slots or not self.slots[slot]:
            return None

        item_to_unequip = self.slots[slot]
        self.slots[slot] = None
        return item_to_unequip

    def get_total_bonus(self, bonus_type: str) -> int:
        """
        Calculates the total bonus of a given type from all equipped items.
        """
        total_bonus = 0
        for item in self.slots.values():
            if item:
                total_bonus += getattr(item, f"{bonus_type}_bonus", 0)
        return total_bonus

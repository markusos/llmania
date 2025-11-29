"""
EquipAction - Equip beneficial items from inventory.

This action mirrors the equip logic from common_actions.equip_beneficial_items().
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


# Armor slot names
ARMOR_SLOTS = ["head", "chest", "legs", "off_hand", "boots"]


class EquipAction(AIAction):
    """
    Equip armor and better weapons from inventory.

    Checks inventory for:
    1. Better weapons (higher attack bonus)
    2. Armor for empty slots
    3. Better armor than currently equipped

    Utility Score: 0.75
    """

    @property
    def name(self) -> str:
        return "Equip"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available if there's something beneficial to equip."""
        return self._find_best_equip(ctx) is not None

    def calculate_utility(self, ctx: "AIContext") -> float:
        """Fixed utility for equipping items."""
        if not self.is_available(ctx):
            return 0.0
        return 0.75

    def _find_best_equip(self, ctx: "AIContext") -> Optional[Tuple[str, str, str]]:
        """
        Find the best item to equip.

        Returns: (item_name, slot, reason) or None
        """
        from src.items import EquippableItem

        for item in ctx.inventory_items:
            if not isinstance(item, EquippableItem):
                continue

            slot = item.properties.get("slot")
            if not slot:
                continue

            equipped = ctx.equipped_items.get(slot)

            # Handle weapons (main_hand)
            if slot == "main_hand":
                current_attack = 0
                if equipped:
                    current_attack = equipped.properties.get("attack_bonus", 0)
                item_attack = item.properties.get("attack_bonus", 0)
                if item_attack > current_attack:
                    return (item.name, slot, "better_weapon")

            # Handle armor slots
            elif slot in ARMOR_SLOTS:
                if equipped is None:
                    # Empty slot - equip immediately
                    return (item.name, slot, "empty_slot")
                else:
                    # Compare defense bonus
                    current_defense = equipped.properties.get("defense_bonus", 0)
                    item_defense = item.properties.get("defense_bonus", 0)
                    if item_defense > current_defense:
                        return (item.name, slot, "better_armor")

        return None

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute equip by using the best equippable item."""
        best_equip = self._find_best_equip(ctx)
        if best_equip:
            item_name, slot, reason = best_equip
            if reason == "better_weapon":
                message_log.add_message(f"AI: Equipping better weapon {item_name}.")
            elif reason == "empty_slot":
                message_log.add_message(
                    f"AI: Equipping {item_name} to empty {slot} slot."
                )
            else:
                message_log.add_message(f"AI: Equipping better armor {item_name}.")
            return ("use", item_name)
        return None

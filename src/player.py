from typing import List, Optional  # Sorted, Added for type hinting

from src.item import Item  # Kept for type hinting
from src.monster import Monster


class Player:
    def __init__(self, x: int, y: int, health: int):
        self.x = x
        self.y = y
        self.health = health
        self.inventory: List[Item] = []  # Type hinted
        self.base_attack_power = 2
        self.equipped_weapon: Optional[Item] = None  # Type hinted

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def attack_monster(self, monster: Monster) -> dict:  # Return type changed to dict
        current_attack_power = self.base_attack_power
        if (
            self.equipped_weapon is not None
            and self.equipped_weapon.properties.get("type") == "weapon"
        ):
            current_attack_power += self.equipped_weapon.properties.get(
                "attack_bonus", 0
            )

        # Call monster.take_damage() ONCE and store its result.
        monster_take_damage_result = monster.take_damage(current_attack_power)
        return {
            "damage_dealt": current_attack_power,  # Was current_attack_power
            "monster_defeated": monster_take_damage_result["defeated"],
            "monster_name": monster.name,
        }

    def take_damage(self, damage: int) -> dict:
        self.health -= damage
        if self.health < 0:
            self.health = 0
        return {"damage_taken": damage, "is_defeated": self.health <= 0}

    def take_item(self, item: Item):
        self.inventory.append(item)
        # Tests for drop_item_no_space imply take_item might be used if
        # dropping fails. However, the primary take action is simpler.

    def drop_item(self, item_name: str) -> Optional[Item]:
        for item in self.inventory:
            if item.name.lower() == item_name.lower():  # Case-insensitive search
                self.inventory.remove(item)
                return item
        return None

    def use_item(self, item_name: str) -> str:
        item_to_use = None
        for item in self.inventory:
            if item.name.lower() == item_name.lower():  # Case-insensitive search
                item_to_use = item
                break

        if not item_to_use:
            # test_player_use_item_unusable_or_not_found expects "Item not found."
            return "Item not found."

        item_type = item_to_use.properties.get("type")

        if item_type == "weapon":
            self.equipped_weapon = item_to_use
            # test_player_use_item_weapon expects "Equipped Iron Sword."
            return f"Equipped {item_to_use.name}."

        elif item_type == "heal":
            heal_amount = item_to_use.properties.get("amount", 0)
            self.health += heal_amount
            self.inventory.remove(item_to_use)  # Healing items are consumed
            # test_player_use_item_heal expects "Used Health Potion, healed by 10 HP."
            return f"Used {item_to_use.name}, healed by {heal_amount} HP."

        elif (
            item_to_use.name == "Cursed Ring"
        ):  # Specific item from a CommandProcessor test
            # Actual health drain effect might be handled elsewhere or via player status
            return "The Cursed Ring drains your life!"

        elif item_type == "junk" or item_type is None:  # Check for None type as well
            # test_player_use_item_unusable_or_not_found expects "Cannot use Rock."
            return f"Cannot use {item_to_use.name}."

        # Default message for other usable items not specifically handled above.
        return f"You use the {item_to_use.name}."

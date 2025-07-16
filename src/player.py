from typing import Dict, List, Optional

from src.equippable import Equippable
from src.item import Item
from src.monster import Monster


class Player:
    """
    Represents the player character in the game.

    Attributes:
        x (int): The player's current x-coordinate on the map.
        y (int): The player's current y-coordinate on the map.
        current_floor_id (int): The ID of the floor the player is currently on.
        health (int): The player's current health points.
        max_health (int): The player's maximum health points.
        inventory (List[Item]): A list of items currently held by the player.
        base_attack_power (int): Innate attack power, before weapon bonuses.
        equipment (Dict[str, Optional[Equippable]]): A dictionary mapping
            equipment slots to equipped items.
    """

    def __init__(self, x: int, y: int, current_floor_id: int, health: int):
        """
        Initializes a Player instance.

        Args:
            x: The initial x-coordinate of the player.
            y: The initial y-coordinate of the player.
            current_floor_id: The initial floor ID for the player.
            health: The initial and maximum health of the player.
        """
        self.x = x
        self.y = y
        self.current_floor_id = current_floor_id
        self.health = health
        self.max_health = health
        self.inventory: List[Item] = []
        self.base_attack_power = 2
        self.base_defense = 0
        self.base_speed = 1
        self.invisibility_turns = 0
        self.equipment: Dict[str, Optional[Equippable]] = {
            "head": None,
            "chest": None,
            "legs": None,
            "main_hand": None,
            "off_hand": None,
            "ring": None,
            "amulet": None,
            "boots": None,
        }

    def move(self, dx: int, dy: int):
        """
        Moves the player by the given delta in x and y coordinates.

        Args:
            dx: The change in the x-coordinate.
            dy: The change in the y-coordinate.
        """
        self.x += dx
        self.y += dy

    def get_attack_power(self) -> int:
        """
        Calculates the player's total attack power, including equipment bonuses.

        Returns:
            The total attack power.
        """
        total_attack_power = self.base_attack_power
        for item in self.equipment.values():
            if item:
                total_attack_power += item.attack_bonus
        return total_attack_power

    def get_defense(self) -> int:
        """
        Calculates the player's total defense, including equipment bonuses.

        Returns:
            The total defense.
        """
        total_defense = self.base_defense
        for item in self.equipment.values():
            if item and hasattr(item, "defense_bonus"):
                total_defense += item.defense_bonus
        return total_defense

    def get_speed(self) -> int:
        """
        Calculates the player's total speed, including equipment bonuses.

        Returns:
            The total speed.
        """
        total_speed = self.base_speed
        for item in self.equipment.values():
            if item and hasattr(item, "speed_bonus"):
                total_speed += item.speed_bonus
        return total_speed

    def attack_monster(self, monster: Monster) -> dict[str, str | int | bool]:
        """
        Attacks a specified monster.

        Args:
            monster: The Monster instance to attack.

        Returns:
            A dictionary containing the results of the attack.
        """
        attack_power = self.get_attack_power()
        monster_take_damage_result = monster.take_damage(attack_power)
        return {
            "damage_dealt": attack_power,
            "monster_defeated": monster_take_damage_result["defeated"],
            "monster_name": monster.name,
        }

    def take_damage(self, damage: int) -> dict[str, bool | int]:
        """
        Reduces the player's health by the given amount of damage, taking
        defense into account.

        Args:
            damage: The amount of damage to inflict on the player.

        Returns:
            A dictionary containing the results of taking damage.
        """
        damage_taken = max(0, damage - self.get_defense())
        self.health -= damage_taken
        if self.health < 0:
            self.health = 0
        return {"damage_taken": damage_taken, "is_defeated": self.health <= 0}

    def take_item(self, item: Item):
        """
        Adds an item to the player's inventory.

        Args:
            item: The Item instance to add.
        """
        self.inventory.append(item)

    def _find_item_in_inventory(self, item_name: str) -> Optional[Item]:
        """
        Searches the player's inventory for an item by name.

        Args:
            item_name: The name of the item to find.

        Returns:
            The Item instance if found, otherwise None.
        """
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                return item
        return None

    def drop_item(self, item_name: str) -> Optional[Item]:
        """
        Removes an item from the player's inventory by name.

        Args:
            item_name: The name of the item to drop.

        Returns:
            The Item instance that was dropped, or None if not found.
        """
        item_to_drop = self._find_item_in_inventory(item_name)
        if not item_to_drop:
            return None

        if isinstance(item_to_drop, Equippable):
            self.unequip(item_to_drop.slot)

        self.inventory.remove(item_to_drop)
        return item_to_drop

    def use_item(self, item_name: str) -> str:
        """
        Uses an item from the player's inventory by name.

        Args:
            item_name: The name of the item to use.

        Returns:
            A string message describing the outcome.
        """
        item_to_use = self._find_item_in_inventory(item_name)
        if not item_to_use:
            return "Item not found."

        if isinstance(item_to_use, Equippable):
            return self.toggle_equip(item_to_use)

        item_type = item_to_use.properties.get("type")

        if item_type == "heal":
            return self.use_health_potion(item_to_use)
        elif item_type == "cursed":
            return self.use_cursed_item(item_to_use)
        elif item_type == "damage":
            return self.use_damage_item(item_to_use)
        elif item_type == "teleport":
            return self.use_teleport_scroll(item_to_use)
        elif item_type == "invisibility":
            return self.use_invisibility_potion(item_to_use)
        elif item_type == "junk" or item_type is None:
            return f"Cannot use {item_to_use.name}."

        return f"You use the {item_to_use.name}."

    def use_health_potion(self, item: Item) -> str:
        """
        Uses a health potion to restore health.

        Args:
            item: The health potion item.

        Returns:
            A message describing the outcome.
        """
        if self.health == self.max_health:
            return f"You use {item.name}, but you are already at full health."

        heal_amount = item.properties.get("amount", 0)
        healed_actually = min(heal_amount, self.max_health - self.health)
        self.health += healed_actually

        if healed_actually > 0:
            self.inventory.remove(item)
            return f"Used {item.name}, healed by {healed_actually} HP."
        else:
            return f"You use {item.name}, but it has no effect."

    def use_cursed_item(self, item: Item) -> str:
        """
        Uses a cursed item, taking damage.

        Args:
            item: The cursed item.

        Returns:
            A message describing the outcome.
        """
        damage = item.properties.get("damage", 0)
        self.health -= damage
        if self.health < 0:
            self.health = 0
        self.inventory.remove(item)
        return f"The {item.name} is cursed! You take {damage} damage."

    def toggle_equip(self, item: Equippable) -> str:
        """
        Equips or unequips an item.

        Args:
            item: The item to toggle.

        Returns:
            A message describing the outcome.
        """
        slot = item.slot
        if self.equipment.get(slot) == item:
            return self.unequip(slot)
        else:
            return self.equip(item)

    def equip(self, item: Equippable) -> str:
        """
        Equips an item to its slot.

        Args:
            item: The item to equip.

        Returns:
            A message describing the outcome.
        """
        slot = item.slot
        if not slot or slot not in self.equipment:
            return f"Cannot equip {item.name}."

        unequip_message = ""
        if self.equipment[slot]:
            unequip_message = self.unequip(slot) + " "

        self.equipment[slot] = item
        if item.properties.get("type") == "amulet":
            self.max_health += item.properties.get("max_health_bonus", 0)
            self.health += item.properties.get("max_health_bonus", 0)
        return f"{unequip_message}Equipped {item.name}."

    def unequip(self, slot: str) -> str:
        """
        Unequips an item from a slot.

        Args:
            slot: The slot to unequip.

        Returns:
            A message describing the outcome.
        """
        if not slot or slot not in self.equipment or not self.equipment[slot]:
            return ""

        item = self.equipment[slot]
        self.equipment[slot] = None
        if item.properties.get("type") == "amulet":
            self.max_health -= item.properties.get("max_health_bonus", 0)
            if self.health > self.max_health:
                self.health = self.max_health
        return f"You unequip {item.name}."

    def use_damage_item(self, item: Item) -> str:
        """
        Uses a damage item, which is consumed.

        Args:
            item: The damage item.

        Returns:
            A message describing the outcome.
        """
        self.inventory.remove(item)
        return f"You use the {item.name}, it's now ready to be thrown."

    def use_teleport_scroll(self, item: Item) -> str:
        """
        Uses a teleport scroll, which is consumed.

        Args:
            item: The teleport scroll.

        Returns:
            A message describing the outcome.
        """
        self.inventory.remove(item)
        return f"You read the {item.name}."

    def use_invisibility_potion(self, item: Item) -> str:
        """
        Uses an invisibility potion, which is consumed.

        Args:
            item: The invisibility potion.

        Returns:
            A message describing the outcome.
        """
        self.inventory.remove(item)
        self.invisibility_turns += item.properties.get("duration", 0)
        return f"You drink the {item.name} and become invisible."

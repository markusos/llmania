from typing import List, Optional  # Sorted, Added for type hinting

from src.item import Item  # Kept for type hinting
from src.monster import Monster


class Player:
    """
    Represents the player character in the game.

    Attributes:
        x (int): The player's current x-coordinate on the map.
        y (int): The player's current y-coordinate on the map.
        health (int): The player's current health points.
        max_health (int): The player's maximum health points.
        inventory (List[Item]): A list of items currently held by the player.
        base_attack_power (int): The player's innate attack power, before weapon bonuses.
        equipped_weapon (Optional[Item]): The weapon currently equipped by the player, if any.
    """

    def __init__(self, x: int, y: int, health: int):
        """
        Initializes a Player instance.

        Args:
            x: The initial x-coordinate of the player.
            y: The initial y-coordinate of the player.
            health: The initial and maximum health of the player.
        """
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health  # Player starts with max health.
        self.inventory: List[Item] = []
        self.base_attack_power = 2  # Default base attack power.
        self.equipped_weapon: Optional[Item] = None

    def move(self, dx: int, dy: int):
        """
        Moves the player by the given delta in x and y coordinates.

        Args:
            dx: The change in the x-coordinate.
            dy: The change in the y-coordinate.
        """
        self.x += dx
        self.y += dy

    def attack_monster(self, monster: Monster) -> dict[str, str | int | bool]:
        """
        Attacks a specified monster.

        The player's attack power is their base attack power plus any bonus
        from an equipped weapon.

        Args:
            monster: The Monster instance to attack.

        Returns:
            A dictionary containing the results of the attack:
                "damage_dealt" (int): The amount of damage dealt to the monster.
                "monster_defeated" (bool): True if the monster was defeated.
                "monster_name" (str): The name of the monster attacked.
        """
        current_attack_power = self.base_attack_power
        if (
            self.equipped_weapon is not None
            and self.equipped_weapon.properties.get("type") == "weapon"
        ):
            current_attack_power += self.equipped_weapon.properties.get(
                "attack_bonus", 0
            )

        monster_take_damage_result = monster.take_damage(current_attack_power)
        return {
            "damage_dealt": current_attack_power,
            "monster_defeated": monster_take_damage_result["defeated"],
            "monster_name": monster.name,
        }

    def take_damage(self, damage: int) -> dict[str, bool | int]:
        """
        Reduces the player's health by the given amount of damage.
        Health cannot go below zero.

        Args:
            damage: The amount of damage to inflict on the player.

        Returns:
            A dictionary containing:
                "damage_taken" (int): The amount of damage taken.
                "is_defeated" (bool): True if the player's health is 0 or less.
        """
        self.health -= damage
        if self.health < 0:
            self.health = 0
        return {"damage_taken": damage, "is_defeated": self.health <= 0}

    def take_item(self, item: Item):
        """
        Adds an item to the player's inventory.

        Args:
            item: The Item instance to add.
        """
        self.inventory.append(item)
        # Note: No message is generated here; CommandProcessor handles messages.

    def _find_item_in_inventory(self, item_name: str) -> Optional[Item]:
        """
        Searches the player's inventory for an item by name (case-insensitive).

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
        If the dropped item is the equipped weapon, it is unequipped.

        Args:
            item_name: The name of the item to drop (case-insensitive).

        Returns:
            The Item instance that was dropped, or None if the item was not found.
        """
        item_to_drop = self._find_item_in_inventory(item_name)
        if not item_to_drop:
            return None  # Item not found, no message here.

        # If the item to drop is the currently equipped weapon, unequip it.
        if self.equipped_weapon == item_to_drop:
            self.equipped_weapon = None
        self.inventory.remove(item_to_drop)
        return item_to_drop

    def use_item(self, item_name: str) -> str:
        """
        Uses an item from the player's inventory by name.

        The effect of using an item depends on its type:
        - "weapon": Equips or unequips the weapon.
        - "cursed": Damages the player and is consumed.
        - "heal": Restores health (up to max_health) and is consumed if effective.
        - "junk": Cannot be used.
        - Other types: A generic "You use the <item name>." message.

        Args:
            item_name: The name of the item to use (case-insensitive).

        Returns:
            A string message describing the outcome of using the item.
        """
        item_to_use = self._find_item_in_inventory(item_name)
        if not item_to_use:
            return "Item not found."

        item_type = item_to_use.properties.get("type")

        if item_type == "weapon":
            if self.equipped_weapon == item_to_use:  # Trying to use equipped weapon
                self.equipped_weapon = None  # Unequip it
                return f"You unequip {item_to_use.name}."
            else:  # Equip new weapon (or re-equip if it was different)
                unequip_message = ""
                if (
                    self.equipped_weapon
                ):  # If another weapon was equipped, unequip it first
                    unequip_message = f"You unequip {self.equipped_weapon.name}. "
                self.equipped_weapon = item_to_use
                return f"{unequip_message}Equipped {item_to_use.name}."

        elif item_type == "cursed":
            damage = item_to_use.properties.get("damage", 0)
            self.health -= damage
            if self.health < 0:
                self.health = 0
            self.inventory.remove(item_to_use)  # Cursed items are consumed
            # Message clearly indicates damage and that item is cursed.
            # If health drops to 0, CommandProcessor will handle game over.
            return f"The {item_to_use.name} is cursed! You take {damage} damage."

        elif item_type == "heal":
            if self.health == self.max_health:
                # Player is already at full health.
                # Item is not consumed in this case as per current logic.
                return (
                    f"You use {item_to_use.name}, but you are already at full health."
                )

            heal_amount = item_to_use.properties.get("amount", 0)
            healed_actually = min(heal_amount, self.max_health - self.health)

            self.health += healed_actually  # Apply healing

            if healed_actually > 0:  # Item consumed only if it had a positive effect
                self.inventory.remove(item_to_use)
                return f"Used {item_to_use.name}, healed by {healed_actually} HP."
            else:
                # This case implies item had 0 heal amount or player was full (already checked).
                # Item is not consumed if no effective healing.
                return f"You use {item_to_use.name}, but it has no effect."

        elif item_type == "junk" or item_type is None:
            return f"Cannot use {item_to_use.name}."

        # Default message for other usable items not explicitly handled above (e.g. quest items if they are 'usable')
        return f"You use the {item_to_use.name}."

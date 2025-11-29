from typing import Optional

from src.equipment import Equipment
from src.inventory import Inventory
from src.items import EquippableItem, Item
from src.monster import Monster


class Player:
    """
    Represents the player character in the game.
    """

    def __init__(self, x: int, y: int, current_floor_id: int, health: int):
        """
        Initializes a Player instance.
        """
        self.x = x
        self.y = y
        self.current_floor_id = current_floor_id
        self.health = health
        self.max_health = health
        self.inventory = Inventory()
        self.equipment = Equipment()
        self.base_attack_power = 2
        self.base_defense = 0
        self.base_speed = 1
        self.base_attack_speed = 5
        self.base_view_radius = 5
        self.invisibility_turns = 0

    def move(self, dx: int, dy: int):
        """
        Moves the player by the given delta in x and y coordinates.
        """
        self.x += dx
        self.y += dy

    def get_view_radius(self) -> int:
        """
        Calculates the player's total view radius, including equipment bonuses.
        """
        return self.base_view_radius + self.equipment.get_total_bonus("view_radius")

    def get_attack_power(self) -> int:
        """
        Calculates the player's total attack power, including equipment bonuses.
        """
        return self.base_attack_power + self.equipment.get_total_bonus("attack")

    def get_defense(self) -> int:
        """
        Calculates the player's total defense, including equipment bonuses.
        """
        return self.base_defense + self.equipment.get_total_bonus("defense")

    def get_speed(self) -> int:
        """
        Calculates the player's total speed, including equipment bonuses.
        """
        return self.base_speed + self.equipment.get_total_bonus("speed")

    def get_attack_speed(self) -> int:
        """
        Calculates the player's total attack speed, including equipment bonuses.
        """
        return self.base_attack_speed + self.equipment.get_total_bonus("attack_speed")

    def attack_monster(self, monster: Monster) -> dict[str, str | int | bool]:
        """
        Attacks a specified monster.
        """
        attack_power = self.get_attack_power()
        damage_type = "physical"
        main_hand_item = self.equipment.slots.get("main_hand")
        if main_hand_item:
            damage_type = main_hand_item.properties.get("damage_type", "physical")
        monster_take_damage_result = monster.take_damage(attack_power, damage_type)
        return {
            "damage_dealt": monster_take_damage_result["damage_taken"],
            "monster_defeated": monster_take_damage_result["defeated"],
            "monster_name": monster.name,
        }

    def take_damage(self, damage: int) -> dict[str, bool | int]:
        """
        Reduces the player's health by the given amount of damage.
        """
        damage_taken = max(0, damage - self.get_defense())
        self.health -= damage_taken
        if self.health < 0:
            self.health = 0
        return {"damage_taken": damage_taken, "is_defeated": self.health <= 0}

    def take_item(self, item: Item):
        """
        Adds an item to the player's inventory.
        """
        self.inventory.add_item(item)

    def drop_item(self, item_name: str) -> Optional[Item]:
        """
        Removes an item from the player's inventory by name.
        """
        item_to_drop = self.inventory.find_item(item_name)
        if not item_to_drop:
            return None

        if isinstance(item_to_drop, EquippableItem) and item_to_drop.slot:
            self.unequip(item_to_drop.slot)

        self.inventory.remove_item(item_to_drop)
        return item_to_drop

    def use_item(self, item_name: str, game_engine) -> str:
        """
        Uses an item from the player's inventory by name.
        """
        item_to_use = self.inventory.find_item(item_name)
        if not item_to_use:
            return "Item not found."

        return item_to_use.apply(self, game_engine)

    def get_max_health(self) -> int:
        """
        Calculates the player's maximum health, including equipment bonuses.
        """
        return self.max_health + self.equipment.get_total_bonus("max_health")

    def heal(self, amount: int) -> int:
        """
        Heals the player by a given amount.
        """
        max_health = self.get_max_health()
        new_health = self.health + amount
        if new_health > max_health:
            new_health = max_health

        healed_amount = new_health - self.health
        self.health = new_health
        return healed_amount

    def toggle_equip(self, item: EquippableItem) -> str:
        """
        Equips or unequips an item.
        """
        slot = item.slot
        if slot and self.equipment.slots.get(slot) == item:
            return self.unequip(slot)
        else:
            return self.equip(item)

    def equip(self, item: EquippableItem) -> str:
        """
        Equips an item to its slot.
        """
        slot = item.slot
        if not slot or slot not in self.equipment.slots:
            return f"Cannot equip {item.name}."

        unequip_message = ""
        previously_equipped_item = self.equipment.equip(item, slot)
        if previously_equipped_item:
            unequip_message = f"You unequip {previously_equipped_item.name}. "

        if item.max_health_bonus > 0:
            self.health += item.max_health_bonus
        return f"{unequip_message}Equipped {item.name}."

    def unequip(self, slot: str) -> str:
        """
        Unequips an item from a slot.
        """
        if not slot or slot not in self.equipment.slots:
            return ""

        item = self.equipment.unequip(slot)
        if item:
            if item.max_health_bonus > 0:
                self.health -= item.max_health_bonus
                if self.health > self.get_max_health():
                    self.health = self.get_max_health()
            return f"You unequip {item.name}."
        return ""

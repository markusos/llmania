from .item import Item
from .monster import Monster


class Player:
    def __init__(self, x: int, y: int, health: int):
        self.x = x
        self.y = y
        self.health = health
        self.inventory = []
        self.base_attack_power = 2
        self.equipped_weapon = None

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def take_item(self, item: Item):
        self.inventory.append(item)

    def drop_item(self, item_name: str) -> Item | None:
        for i, item in enumerate(self.inventory):
            if item.name == item_name:
                return self.inventory.pop(i)
        return None

    def use_item(self, item_name: str) -> str:
        item_to_use = None
        item_idx = -1
        for i, item in enumerate(self.inventory):
            if item.name == item_name:
                item_to_use = item
                item_idx = i
                break

        if item_to_use is None:
            return "Item not found."

        item_type = item_to_use.properties.get("type")
        if item_type == "heal":
            heal_amount = item_to_use.properties.get("amount", 0)
            self.health += heal_amount
            self.inventory.pop(item_idx)
            return f"Used {item_name}, healed by {heal_amount} HP."
        elif item_type == "weapon":
            self.equipped_weapon = item_to_use
            # Do not remove weapon from inventory upon equipping
            return f"Equipped {item_name}."
        else:
            return f"Cannot use {item_name}."

    def attack_monster(self, monster: Monster) -> int:
        current_attack_power = self.base_attack_power
        if (
            self.equipped_weapon is not None
            and self.equipped_weapon.properties.get("type") == "weapon"
        ):
            current_attack_power += self.equipped_weapon.properties.get(
                "attack_bonus", 0
            )

        monster.take_damage(current_attack_power)
        return current_attack_power

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health < 0:
            self.health = 0

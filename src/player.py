from typing import Optional, List # Added for type hinting
from src.item import Item # Kept for type hinting
from src.monster import Monster


class Player:
    def __init__(self, x: int, y: int, health: int):
        self.x = x
        self.y = y
        self.health = health
        self.inventory: List[Item] = [] # Type hinted
        self.base_attack_power = 2
        self.equipped_weapon: Optional[Item] = None # Type hinted

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def attack_monster(self, monster: Monster) -> dict: # Return type changed to dict
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
            "damage_dealt": current_attack_power, # damage_dealt was current_attack_power
            "monster_defeated": monster_take_damage_result["defeated"],
            "monster_name": monster.name,
        }

    def take_damage(self, damage: int) -> dict:
        self.health -= damage
        if self.health < 0:
            self.health = 0
        return {"damage_taken": damage, "is_defeated": self.health <= 0}

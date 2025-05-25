from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.player import Player  # For type hinting

class Monster:
    def __init__(
        self, name: str, health: int, attack_power: int, x: int = 0, y: int = 0
    ):
        self.name = name
        self.health = health
        self.attack_power = attack_power
        self.x = x
        self.y = y

    def take_damage(self, damage: int) -> dict:
        self.health -= damage
        if self.health < 0:
            self.health = 0
        return {"damage_taken": damage, "defeated": self.health <= 0}

    def attack(self, player: "Player") -> dict:  # player is Player type, forward ref
        damage_to_deal = self.attack_power
        player_damage_result = player.take_damage(damage_to_deal)
        return {
            "damage_dealt_to_player": damage_to_deal,
            "player_is_defeated": player_damage_result[
                "is_defeated"
            ],  # Ensure key matches Player.take_damage
        }

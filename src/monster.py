from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.player import Player  # For type hinting, avoids circular import


class Monster:
    """
    Represents a monster in the game.

    Attributes:
        name (str): The name of the monster (e.g., "Goblin", "Dragon").
        health (int): The current health points of the monster.
        attack_power (int): The amount of damage the monster deals per attack.
        x (int): The monster's x-coordinate on the map.
        y (int): The monster's y-coordinate on the map.
    """

    def __init__(
        self, name: str, health: int, attack_power: int, x: int = 0, y: int = 0
    ):
        """
        Initializes a Monster instance.

        Args:
            name: The name of the monster.
            health: The initial health of the monster.
            attack_power: The attack power of the monster.
            x: Initial x-coordinate (defaults to 0).
            y: Initial y-coordinate (defaults to 0).
        """
        self.name = name
        self.health = health
        self.attack_power = attack_power
        self.x = x  # Position on the map
        self.y = y  # Position on the map

    def take_damage(self, damage: int) -> dict[str, bool | int]:
        """
        Reduces the monster's health by the given amount of damage.
        Health cannot go below zero.

        Args:
            damage: The amount of damage to inflict.

        Returns:
            A dictionary containing:
                "damage_taken" (int): The amount of damage dealt.
                "defeated" (bool): True if the monster's health is 0 or less, False otherwise.
        """
        self.health -= damage
        if self.health < 0:
            self.health = 0  # Health should not be negative
        return {"damage_taken": damage, "defeated": self.health <= 0}

    def attack(self, player: "Player") -> dict[str, bool | int]:
        """
        The monster attacks the player.

        Args:
            player: The Player instance being attacked.

        Returns:
            A dictionary containing:
                "damage_dealt_to_player" (int): The amount of damage dealt to the player.
                "player_is_defeated" (bool): True if the player was defeated by this attack.
        """
        damage_to_deal = self.attack_power
        # Player's take_damage method is called, which handles health reduction.
        player_damage_result = player.take_damage(damage_to_deal)
        return {
            "damage_dealt_to_player": damage_to_deal,
            "player_is_defeated": player_damage_result["is_defeated"],
        }

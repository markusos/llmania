import random
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
        self,
        name: str,
        health: int,
        attack_power: int,
        x: int = 0,
        y: int = 0,
        defense: int = 0,
        evasion: float = 0.0,
        resistance: str = None,
        vulnerability: str = None,
        random_generator: random.Random = None,
    ):
        """
        Initializes a Monster instance.

        Args:
            name: The name of the monster.
            health: The initial health of the monster.
            attack_power: The attack power of the monster.
            x: Initial x-coordinate (defaults to 0).
            y: Initial y-coordinate (defaults to 0).
            defense: The defense of the monster.
            evasion: The evasion chance of the monster.
            resistance: The damage type the monster is resistant to.
            vulnerability: The damage type the monster is vulnerable to.
        """
        self.name = name
        self.health = health
        self.attack_power = attack_power
        self.x = x
        self.y = y
        self.defense = defense
        self.evasion = evasion
        self.resistance = resistance
        self.vulnerability = vulnerability
        self.random = random_generator if random_generator else random.Random()

    def take_damage(
        self, damage: int, damage_type: str = "physical"
    ) -> dict[str, bool | int]:
        """
        Reduces the monster's health by the given amount of damage.
        Health cannot go below zero.

        Args:
            damage: The amount of damage to inflict.
            damage_type: The type of damage being dealt.

        Returns:
            A dictionary containing:
                "damage_taken" (int): The amount of damage dealt.
                "defeated" (bool): True if health is <= 0, False otherwise.
        """
        if self.random.random() < self.evasion:
            return {"damage_taken": 0, "defeated": False}

        if self.resistance == damage_type:
            damage = damage // 2
        if self.vulnerability == damage_type:
            damage = damage * 2

        damage_taken = max(0, damage - self.defense)
        self.health -= damage_taken
        if self.health < 0:
            self.health = 0
        return {"damage_taken": damage_taken, "defeated": self.health <= 0}

    def attack(self, player: "Player") -> dict[str, bool | int]:
        """
        The monster attacks the player.

        Args:
            player: The Player instance being attacked.

        Returns:
            A dictionary containing:
                "damage_dealt_to_player" (int): Damage dealt to the player.
                "player_is_defeated" (bool): True if player was defeated.
        """
        damage_to_deal = self.attack_power
        # Player's take_damage method is called, which handles health reduction.
        player_damage_result = player.take_damage(damage_to_deal)
        return {
            "damage_dealt_to_player": damage_to_deal,
            "player_is_defeated": player_damage_result["is_defeated"],
        }

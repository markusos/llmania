import math
import random
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.monster_ai.main import MonsterAILogic
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
        random_generator: "random.Random",
        x: int = 0,
        y: int = 0,
        defense: int = 0,
        evasion: float = 0.0,
        resistance: str = "",
        vulnerability: str = "",
        line_of_sight: int = 5,
        attack_range: int = 1,
        move_speed: int = 1,
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
            line_of_sight: The distance the monster can see.
            attack_range: The distance the monster can attack from.
            move_speed: The speed of the monster.
            random_generator: The random number generator.
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
        self.line_of_sight = line_of_sight
        self.attack_range = attack_range
        self.move_speed = move_speed
        self.move_energy = 0
        self.random = random_generator
        self.ai: "Optional[MonsterAILogic]" = None

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

    def distance_to(self, x: int, y: int) -> float:
        """
        Calculates the distance to a given point.
        """
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)

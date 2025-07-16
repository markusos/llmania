import json
import random
from typing import Optional

from src.monster import Monster


class MonsterFactory:
    """
    Factory for creating monsters from a data file.
    """

    def __init__(self, monster_data_path: str):
        """
        Initializes the MonsterFactory.

        Args:
            monster_data_path: The path to the JSON file containing monster data.
        """
        with open(monster_data_path, "r") as f:
            self.monster_data = json.load(f)

    def create_monster(
        self, monster_id: str, x: int = 0, y: int = 0
    ) -> Optional[Monster]:
        """
        Creates a monster instance based on the given monster ID.

        Args:
            monster_id: The ID of the monster to create.
            x: The x-coordinate of the monster.
            y: The y-coordinate of the monster.

        Returns:
            A Monster instance, or None if the monster ID is not found.
        """
        monster_info = self.monster_data.get(monster_id)
        if not monster_info:
            return None

        return Monster(
            name=monster_info["name"],
            health=monster_info["health"],
            attack_power=monster_info["attack_power"],
            x=x,
            y=y,
        )

    def create_random_monster(self, x: int = 0, y: int = 0) -> Optional[Monster]:
        """
        Creates a random monster from the available monster data based on rarity.

        Args:
            x: The x-coordinate of the monster.
            y: The y-coordinate of the monster.

        Returns:
            A random Monster instance, or None if there is no monster data.
        """
        if not self.monster_data:
            return None

        rarity_sum = sum(monster["rarity"] for monster in self.monster_data.values())
        roll = random.randint(1, rarity_sum)

        current_sum = 0
        for monster_id, monster_info in self.monster_data.items():
            current_sum += monster_info["rarity"]
            if roll <= current_sum:
                return self.create_monster(monster_id, x, y)

        return None

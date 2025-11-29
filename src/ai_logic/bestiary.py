"""Monster stat lookup - simulates player knowledge of monster stats."""

import json
from pathlib import Path
from typing import Any, Dict


class Bestiary:
    """
    Simulates player knowledge of monster stats.

    Fair play: A real player could memorize this info from experience
    or documentation. The AI uses this to look up monster stats by name
    rather than accessing the monster object's internal state directly.
    """

    _instance: "Bestiary | None" = None
    _data: Dict[str, Dict[str, Any]]

    def __init__(self) -> None:
        self._data = {}

    @classmethod
    def get_instance(cls) -> "Bestiary":
        """Get singleton instance of Bestiary."""
        if cls._instance is None:
            cls._instance = Bestiary()
            cls._instance._load_data()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for testing)."""
        cls._instance = None

    def _load_data(self) -> None:
        """Load monster data from monsters.json."""
        path = Path(__file__).parent.parent / "data" / "monsters.json"
        with open(path) as f:
            raw_data = json.load(f)
        # Index by monster name for quick lookup
        for _key, monster_data in raw_data.items():
            name = monster_data.get("name", _key)
            self._data[name.lower()] = monster_data

    def get_stats(self, monster_name: str) -> Dict[str, Any]:
        """Look up monster stats by name."""
        return self._data.get(
            monster_name.lower(),
            {
                "name": monster_name,
                "health": 10,
                "attack_power": 2,
                "defense": 0,
            },
        )

    def get_attack_power(self, monster_name: str) -> int:
        """Get monster's attack power."""
        return int(self.get_stats(monster_name).get("attack_power", 2))

    def get_health(self, monster_name: str) -> int:
        """Get monster's max health."""
        return int(self.get_stats(monster_name).get("health", 10))

    def get_defense(self, monster_name: str) -> int:
        """Get monster's defense."""
        return int(self.get_stats(monster_name).get("defense", 0))

    def get_vulnerability(self, monster_name: str) -> str:
        """Get monster's damage vulnerability (if any)."""
        return str(self.get_stats(monster_name).get("vulnerability", ""))

    def get_resistance(self, monster_name: str) -> str:
        """Get monster's damage resistance (if any)."""
        return str(self.get_stats(monster_name).get("resistance", ""))

    def get_danger_rating(self, monster_name: str) -> int:
        """
        Calculate danger rating 1-5 based on monster stats.

        This helps the AI prioritize which monsters to engage or avoid.
        """
        stats = self.get_stats(monster_name)
        danger = 1

        # Factor in attack power
        attack = stats.get("attack_power", 2)
        if attack >= 5:
            danger += 2
        elif attack >= 3:
            danger += 1

        # Factor in health/tankiness
        effective_hp = stats.get("health", 10) + stats.get("defense", 0) * 2
        if effective_hp >= 25:
            danger += 1

        # Factor in evasion
        if stats.get("evasion", 0) > 0.1:
            danger += 1

        return min(danger, 5)

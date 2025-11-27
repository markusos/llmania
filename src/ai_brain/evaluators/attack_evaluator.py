from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator
from ..target_finder import TargetFinder

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class AttackEvaluator(Evaluator):
    """
    This evaluator encourages the AI to attack nearby monsters.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="AttackEvaluator", weight=weight)
        self.target_finder: TargetFinder | None = None

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        if self.target_finder is None:
            self.target_finder = TargetFinder(game_engine)

        goals: List[Goal] = []
        player = game_engine.player
        current_map = game_engine.get_current_map()

        # Find all monsters on the current floor
        monsters = [
            (monster, abs(monster.x - player.x) + abs(monster.y - player.y))
            for monster in current_map.get_monsters()
        ]

        if not monsters:
            return []

        # Find the closest monster
        closest_monster, dist = min(monsters, key=lambda m: m[1])

        # The desire to attack is inversely proportional to the distance to the monster
        # and directly proportional to the player's health.
        health_ratio = player.health / player.get_max_health()
        score = (1.0 / (dist + 1)) * health_ratio
        goals.append(
            Goal(
                name="attack_monster",
                score=score,
                context={
                    "target_position": (
                        closest_monster.x,
                        closest_monster.y,
                        player.current_floor_id,
                    ),
                    "monster": closest_monster,
                },
            )
        )

        return goals

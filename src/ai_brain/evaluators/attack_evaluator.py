from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class AttackEvaluator(Evaluator):
    """
    This evaluator assesses threats and encourages the AI to attack nearby monsters.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="AttackEvaluator", weight=weight)

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        goals: List[Goal] = []
        player = game_engine.player
        current_map = game_engine.get_current_map()

        # Find adjacent monsters
        adjacent_monsters = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            x, y = player.x + dx, player.y + dy
            tile = current_map.get_tile(x, y)
            if tile and tile.monster:
                adjacent_monsters.append(tile.monster)

        # Prioritize the weakest monster
        if adjacent_monsters:
            weakest_monster = min(adjacent_monsters, key=lambda m: m.health)
            # The score is higher if the player's health is high, encouraging
            # aggressive behavior when safe.
            health_ratio = player.health / player.max_health
            goals.append(
                Goal(
                    name="attack_monster",
                    score=0.8 * health_ratio,
                    context={"monster": weakest_monster},
                )
            )

        return goals

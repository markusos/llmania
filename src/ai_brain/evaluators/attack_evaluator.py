from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class AttackEvaluator(Evaluator):
    """
    This evaluator makes the AI extremely cautious. It will only attack if its
    health is very high, and its desire to fight will drop off sharply as it
    takes damage.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="AttackEvaluator", weight=weight)

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        goals: List[Goal] = []
        player = game_engine.player
        current_map = game_engine.get_current_map()

        health_ratio = player.health / player.get_max_health()
        if health_ratio < 0.9:  # Only attack if health is above 90%
            return []

        adjacent_monsters = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            x, y = player.x + dx, player.y + dy
            tile = current_map.get_tile(x, y)
            if tile and tile.monster:
                adjacent_monsters.append(tile.monster)

        if adjacent_monsters:
            weakest_monster = min(adjacent_monsters, key=lambda m: m.health)
            # The score is heavily influenced by the AI's current health.
            # The high exponent makes the desire to attack drop off very quickly.
            score = 0.8 * (health_ratio**5)
            goals.append(
                Goal(
                    name="attack_monster",
                    score=score,
                    context={"monster": weakest_monster},
                )
            )

        return goals

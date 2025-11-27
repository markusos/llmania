from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class SurvivalEvaluator(Evaluator):
    """
    This evaluator focuses on the AI's survival, primarily by encouraging
    the use of healing items when health is low.
    """

    def __init__(self, weight: float = 1.8):  # Increased weight
        super().__init__(name="SurvivalEvaluator", weight=weight)

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        goals: List[Goal] = []
        player = game_engine.player

        # Start considering healing at 75% health
        health_threshold = player.max_health * 0.75
        if player.health >= health_threshold:
            return []

        health_percentage = player.health / player.max_health
        urgency = 1.0 - health_percentage

        healing_potions = [
            item
            for item in player.inventory.items
            if item.name == "Health Potion"
        ]

        if healing_potions:
            goals.append(
                Goal(
                    name="use_health_potion",
                    score=urgency,
                    context={"item": healing_potions[0]},
                )
            )

        return goals

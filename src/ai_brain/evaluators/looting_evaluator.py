from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class LootingEvaluator(Evaluator):
    """
    This evaluator encourages the AI to pick up items from the ground.
    """

    def __init__(self, weight: float = 0.5):
        super().__init__(name="LootingEvaluator", weight=weight)

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        goals: List[Goal] = []
        player = game_engine.player
        current_map = game_engine.get_current_map()
        current_tile = current_map.get_tile(player.x, player.y)

        if current_tile and current_tile.item:
            # The score can be adjusted based on the item's value or type in the future.
            # For now, any item is worth picking up.
            goals.append(
                Goal(
                    name="take_item",
                    score=0.6,  # A moderate desire to pick up items
                    context={"item": current_tile.item},
                )
            )

        return goals

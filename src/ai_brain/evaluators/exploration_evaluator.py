from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class ExplorationEvaluator(Evaluator):
    """
    This evaluator encourages the AI to explore the map to uncover new areas.
    """

    def __init__(self, weight: float = 0.2):
        super().__init__(name="ExplorationEvaluator", weight=weight)

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        # For now, we'll keep this simple. The goal to explore always has a
        # constant, low-priority score. This ensures that exploration happens
        # only when no other high-priority actions (like healing or fighting)
        # are available.
        return [Goal(name="explore", score=0.1)]

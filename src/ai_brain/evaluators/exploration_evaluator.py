from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator
from ..explorer import Explorer

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class ExplorationEvaluator(Evaluator):
    """
    This evaluator encourages the AI to explore the map methodically.
    It prioritizes exploring the current floor until it's fully revealed,
    then seeks out unvisited portals to other floors.
    """

    def __init__(self, weight: float = 0.3):
        super().__init__(name="ExplorationEvaluator", weight=weight)
        self.explorer: Explorer | None = None

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        if self.explorer is None:
            self.explorer = Explorer(game_engine)

        goals: List[Goal] = []

        # 1. Find the closest unexplored tile on the current floor
        closest_unexplored = self.explorer.find_closest_unexplored_tile()
        if closest_unexplored:
            score = 0.5  # Moderate priority
            goals.append(
                Goal(
                    name="explore_map",
                    score=score,
                    context={"target_position": closest_unexplored},
                )
            )
            return goals

        # 2. If the current floor is explored, find the closest unvisited portal
        closest_portal = self.explorer.find_closest_unvisited_portal()
        if closest_portal:
            score = 0.8  # Higher priority to move to a new floor
            goals.append(
                Goal(
                    name="move_to_unvisited_portal",
                    score=score,
                    context={"target_position": closest_portal},
                )
            )

        return goals

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator
from ..target_finder import TargetFinder

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class QuestEvaluator(Evaluator):
    """
    This evaluator focuses on the main quest objective: finding the Amulet of Yendor.
    """

    def __init__(self, weight: float = 2.0):  # High weight to prioritize the quest
        super().__init__(name="QuestEvaluator", weight=weight)
        self.target_finder: TargetFinder | None = None

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        if self.target_finder is None:
            self.target_finder = TargetFinder(game_engine)

        goals: List[Goal] = []
        winning_pos = game_engine.winning_full_pos

        # Check if the winning position is known
        if winning_pos:
            # Check if the tile at the winning position is explored
            win_x, win_y, win_floor = winning_pos
            visible_map = game_engine.visible_maps.get(win_floor)
            if visible_map and visible_map.get_tile(win_x, win_y).is_explored:
                # The location of the Amulet is known, create a high-priority goal
                player = game_engine.player
                dist = (
                    abs(win_x - player.x)
                    + abs(win_y - player.y)
                    + abs(win_floor - player.current_floor_id) * 10
                )
                score = 1.0 / (dist + 1)
                goals.append(
                    Goal(
                        name="move_to_amulet",
                        score=score,
                        context={"target_position": winning_pos},
                    )
                )

        return goals

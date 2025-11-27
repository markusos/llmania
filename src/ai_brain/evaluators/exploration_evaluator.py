from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator
from ..explorer import Explorer
from ..target_finder import TargetFinder

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class ExplorationEvaluator(Evaluator):
    """
    This evaluator encourages the AI to explore the map by identifying and
    prioritizing various points of interest. It prioritizes exploring the
    current floor over taking a portal.
    """

    def __init__(self, weight: float = 0.3):
        super().__init__(name="ExplorationEvaluator", weight=weight)
        self.target_finder: TargetFinder | None = None
        self.explorer: Explorer | None = None

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        if self.target_finder is None:
            self.target_finder = TargetFinder(game_engine)
        if self.explorer is None:
            self.explorer = Explorer(game_engine)

        goals: List[Goal] = []
        targets = []

        targets.extend(self.target_finder.find_other_items())
        targets.extend(self.target_finder.find_monsters())
        targets.extend(self.explorer.find_unvisited_portals())

        sorted_targets = sorted(targets, key=self._target_sort_key)

        if sorted_targets:
            best_target = sorted_targets[0]
            target_x, target_y, target_floor, target_type, _ = best_target
            score = 1.0 / (best_target[4] + 1)
            goals.append(
                Goal(
                    name=f"move_to_{target_type}",
                    score=score,
                    context={
                        "target_position": (target_x, target_y, target_floor),
                        "type": target_type,
                    },
                )
            )

        exploration_path = self.explorer.find_exploration_targets()
        if exploration_path:
            target_coord = exploration_path[-1]
            # Prioritize exploring the current floor
            score = 0.2 if self._is_current_floor_explored(game_engine) else 0.5
            goals.append(
                Goal(
                    name="explore_map",
                    score=score,
                    context={"target_position": target_coord},
                )
            )

        return goals

    def _target_sort_key(self, target_data):
        _, _, _, target_type, dist = target_data
        priority = 5
        if target_type == "unvisited_portal":
            priority = 4  # Lower priority than other items and monsters
        elif target_type == "monster":
            priority = 2
        elif target_type == "other_item":
            priority = 3
        return (priority, dist)

    def _is_current_floor_explored(self, game_engine: "GameEngine") -> bool:
        """
        Checks if the current floor is mostly explored.
        """
        current_map = game_engine.get_current_map()
        total_tiles = current_map.width * current_map.height
        unexplored_tiles = 0
        for y in range(current_map.height):
            for x in range(current_map.width):
                tile = current_map.get_tile(x, y)
                if tile and not tile.is_explored:
                    unexplored_tiles += 1
        # Consider the floor explored if less than 10% is unexplored
        return (unexplored_tiles / total_tiles) < 0.1

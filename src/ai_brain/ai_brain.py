from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder

from .data_structures import Action, Goal
from .evaluators.attack_evaluator import AttackEvaluator
from .evaluators.exploration_evaluator import ExplorationEvaluator
from .evaluators.looting_evaluator import LootingEvaluator
from .evaluators.survival_evaluator import SurvivalEvaluator

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class AIBrain:
    """The main decision-making component for the AI."""

    def __init__(self, game_engine: "GameEngine"):
        self.game_engine = game_engine
        self.evaluators = [
            SurvivalEvaluator(),
            LootingEvaluator(),
            AttackEvaluator(),
            ExplorationEvaluator(),
        ]
        self.path_finder = PathFinder()
        self.current_path: Optional[List[Tuple[int, int, int]]] = None
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None

    def get_next_action(self) -> Tuple[str, Optional[str]]:
        """
        Evaluates all goals and selects the best action to perform.
        """
        # If following a path, check for interruptions
        if self.current_path:
            # High-priority goals that can interrupt pathing
            interrupt_goals = self._get_interrupt_goals()
            if interrupt_goals:
                best_interrupt = max(interrupt_goals, key=lambda g: g.score)
                if best_interrupt.score > 0.8:  # Interrupt threshold
                    self.current_path = None  # Clear path and handle new goal
                    return self._plan_action_for_goal(best_interrupt).command

            # Otherwise, continue following the path
            action = self._follow_path()
            if action:
                return action.command
            else:
                self.current_path = None  # Path is complete or blocked

        # If not following a path, evaluate all goals
        all_goals: List[Goal] = []
        for evaluator in self.evaluators:
            goals = evaluator.evaluate(self.game_engine)
            for goal in goals:
                goal.score *= evaluator.weight
                all_goals.append(goal)

        if not all_goals:
            return ("look", None)

        best_goal = max(all_goals, key=lambda g: g.score)
        action = self._plan_action_for_goal(best_goal)
        return action.command

    def _get_interrupt_goals(self) -> List[Goal]:
        """
        Checks for high-priority goals that should interrupt pathfinding.
        """
        interrupt_goals: List[Goal] = []
        # Survival and attacking are high-priority
        for evaluator in [SurvivalEvaluator(), AttackEvaluator(), LootingEvaluator()]:
            goals = evaluator.evaluate(self.game_engine)
            for goal in goals:
                goal.score *= evaluator.weight
                interrupt_goals.append(goal)
        return interrupt_goals

    def _plan_action_for_goal(self, goal: Goal) -> Action:
        """
        Determines the specific command to execute based on the chosen goal.
        """
        player = self.game_engine.player

        # Immediate actions
        if goal.name == "use_health_potion":
            return Action(command=("use", goal.context["item"].name))
        if goal.name == "take_item":
            return Action(command=("take", goal.context["item"].name))
        if goal.name == "attack_monster":
            return Action(command=("attack", goal.context["monster"].name))

        # Pathfinding actions
        if "target_position" in goal.context:
            target_pos = goal.context["target_position"]
            path = self.path_finder.find_path_bfs(
                self.game_engine.visible_maps,
                (player.x, player.y),
                player.current_floor_id,
                (target_pos[0], target_pos[1]),
                target_pos[2],
            )
            if path:
                self.current_path = path
                return self._follow_path() or Action(command=("look", None))

        # Fallback to random exploration if no path is found
        return Action(command=self._explore_randomly())

    def _follow_path(self) -> Optional[Action]:
        """
        Follows the current path, returning the next move command.
        """
        if not self.current_path:
            return None

        player = self.game_engine.player
        current_pos_xyz = (player.x, player.y, player.current_floor_id)

        # If we are at the start of the path, pop it
        if self.current_path and self.current_path[0] == current_pos_xyz:
            self.current_path.pop(0)

        if not self.current_path:
            return None

        next_step = self.current_path[0]
        dx = next_step[0] - current_pos_xyz[0]
        dy = next_step[1] - current_pos_xyz[1]

        move_command = self._coordinates_to_move_command(dx, dy)
        if move_command:
            self.last_move_command = move_command
            return Action(command=move_command)
        return None

    def _coordinates_to_move_command(
        self, dx: int, dy: int
    ) -> Optional[Tuple[str, str]]:
        if dx == 0 and dy == -1:
            return ("move", "north")
        if dx == 0 and dy == 1:
            return ("move", "south")
        if dx == -1 and dy == 0:
            return ("move", "west")
        if dx == 1 and dy == 0:
            return ("move", "east")
        return None

    def _explore_randomly(self) -> Tuple[str, Optional[str]]:
        """
        Selects a random valid move to explore the map.
        """
        player = self.game_engine.player
        current_map = self.game_engine.get_current_map()
        possible_moves = []
        for direction, (dx, dy) in [
            ("north", (0, -1)),
            ("south", (0, 1)),
            ("west", (-1, 0)),
            ("east", (1, 0)),
        ]:
            if current_map.is_valid_move(player.x + dx, player.y + dy):
                possible_moves.append(("move", direction))

        if not possible_moves:
            return ("look", None)

        if len(possible_moves) > 1 and self.last_move_command:
            filtered_moves = [m for m in possible_moves if m != self.last_move_command]
            if filtered_moves:
                return random.choice(filtered_moves)
        return random.choice(possible_moves)

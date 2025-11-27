from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Tuple

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
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None

    def get_next_action(self) -> Tuple[str, Optional[str]]:
        """
        Evaluates all goals and selects the best action to perform.
        """
        all_goals: List[Goal] = []
        for evaluator in self.evaluators:
            goals = evaluator.evaluate(self.game_engine)
            for goal in goals:
                # The final score is the goal's score multiplied by the
                # evaluator's weight.
                goal.score *= evaluator.weight
                all_goals.append(goal)

        if not all_goals:
            return ("look", None)  # Default action if no goals are generated

        # Select the goal with the highest score
        best_goal = max(all_goals, key=lambda g: g.score)

        # Plan the action to achieve the best goal
        action = self._plan_action_for_goal(best_goal)

        return action.command

    def _plan_action_for_goal(self, goal: Goal) -> Action:
        """
        Determines the specific command to execute based on the chosen goal.
        """
        if goal.name == "use_health_potion":
            item_name = goal.context["item"].name
            return Action(command=("use", item_name), score=goal.score)

        elif goal.name == "take_item":
            item_name = goal.context["item"].name
            return Action(command=("take", item_name), score=goal.score)

        elif goal.name == "attack_monster":
            monster_name = goal.context["monster"].name
            return Action(command=("attack", monster_name), score=goal.score)

        elif goal.name == "explore":
            # For exploration, we'll use random movement for now.
            command = self._explore_randomly()
            return Action(command=command, score=goal.score)

        return Action(command=("look", None), score=0.0)  # Fallback

    def _explore_randomly(self) -> Tuple[str, Optional[str]]:
        """
        Selects a random valid move to explore the map.
        Tries to avoid immediately reversing the last move.
        """
        player = self.game_engine.player
        current_map = self.game_engine.get_current_map()
        possible_moves = []

        # Define potential moves
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

        # Avoid reversing the last move if other options are available
        if len(possible_moves) > 1 and self.last_move_command:
            # Create a list of moves that aren't the last one
            filtered_moves = [m for m in possible_moves if m != self.last_move_command]
            if filtered_moves:
                chosen_move = random.choice(filtered_moves)
                self.last_move_command = chosen_move
                return chosen_move

        # Otherwise, pick any random move
        chosen_move = random.choice(possible_moves)
        self.last_move_command = chosen_move
        return chosen_move

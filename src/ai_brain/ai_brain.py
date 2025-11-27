from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder

from .data_structures import Action, Goal
from .evaluators.attack_evaluator import AttackEvaluator
from .evaluators.exploration_evaluator import ExplorationEvaluator
from .evaluators.looting_evaluator import LootingEvaluator
from .evaluators.quest_evaluator import QuestEvaluator
from .evaluators.survival_evaluator import SurvivalEvaluator
from .explorer import Explorer

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class AIBrain:
    """The main decision-making component for the AI."""

    def __init__(self, game_engine: "GameEngine"):
        self.game_engine = game_engine
        self.evaluators = [
            QuestEvaluator(),
            SurvivalEvaluator(),
            LootingEvaluator(),
            AttackEvaluator(),
            ExplorationEvaluator(),
        ]
        self.path_finder = PathFinder()
        self.explorer = Explorer(game_engine)
        self.current_path: Optional[List[Tuple[int, int, int]]] = None
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None
        self.command_history: List[Optional[Tuple[str, Optional[str]]]] = []
        self.position_history: List[Tuple[Tuple[int, int], int]] = []
        self.loop_breaker_moves_left = 0

    def get_next_action(self) -> Tuple[str, Optional[str]]:
        """
        Evaluates all goals and selects the best action to perform.
        """
        player = self.game_engine.player
        player_pos = ((player.x, player.y), player.current_floor_id)

        if self.position_history:
            last_pos, last_floor = self.position_history[-1]
            if last_floor != player.current_floor_id:
                self.explorer.mark_portal_as_visited(
                    last_pos[0], last_pos[1], last_floor
                )
                if self.game_engine.verbose > 0:
                    print(
                        f"AI: Portal at {last_pos} on floor {last_floor} "
                        "marked as visited."
                    )

        self.position_history.append(player_pos)
        if len(self.position_history) > 10:
            self.position_history.pop(0)

        if self._is_in_loop():
            self._break_loop()

        if self.loop_breaker_moves_left > 0:
            self.loop_breaker_moves_left -= 1
            action_command = self._explore_randomly()
            self.command_history.append(action_command)
            return action_command

        if self.game_engine.verbose > 0:
            print("\n--- AI Decision Cycle ---")
            print(
                f"Player HP: {player.health}/{player.get_max_health()} | "
                f"Pos: ({player.x}, {player.y}, Floor {player.current_floor_id})"
            )
            if self.current_path:
                print(f"Following path. Steps left: {len(self.current_path)}")

        if self.current_path:
            interrupt_goals = self._get_interrupt_goals(log=True)
            if interrupt_goals:
                best_interrupt = max(interrupt_goals, key=lambda g: g.score)
                if best_interrupt.score > 0.8:
                    if self.game_engine.verbose > 0:
                        print(
                            "Path interrupted by high-priority goal: "
                            f"{best_interrupt.name} (Score: {best_interrupt.score:.2f})"
                        )
                    self.current_path = None
                    action = self._plan_action_for_goal(best_interrupt)
                    self.command_history.append(action.command)
                    return action.command

            action = self._follow_path()
            if action:
                self.command_history.append(action.command)
                return action.command
            else:
                self.current_path = None

        all_goals: List[Goal] = []
        if self.game_engine.verbose > 0:
            print("Evaluating Goals:")

        for evaluator in self.evaluators:
            goals = evaluator.evaluate(self.game_engine)
            for goal in goals:
                original_score = goal.score
                goal.score *= evaluator.weight
                all_goals.append(goal)
                if self.game_engine.verbose > 0:
                    context_str = ", ".join(
                        f"{k}: {v}" for k, v in goal.context.items()
                    )
                    print(
                        f"  - {evaluator.name}: {goal.name} "
                        f"(raw: {original_score:.2f}, weighted: {goal.score:.2f}) "
                        f"| Context: {context_str}"
                    )

        if not all_goals:
            action_command = ("look", None)
            self.command_history.append(action_command)
            return action_command

        best_goal = max(all_goals, key=lambda g: g.score)
        if self.game_engine.verbose > 0:
            print(f"Best Goal: {best_goal.name} (Score: {best_goal.score:.2f})")

        action = self._plan_action_for_goal(best_goal)
        if self.game_engine.verbose > 0:
            print(f"Chosen Action: {action.command}")

        self.command_history.append(action.command)
        return action.command

    def _is_in_loop(self, lookback: int = 4) -> bool:
        if len(self.command_history) < lookback:
            return False
        last_commands = self.command_history[-lookback:]
        if len(set(last_commands)) <= 2:
            if len(self.position_history) >= 4:
                recent_xy_pos = [pos[0] for pos in self.position_history[-4:]]
                if len(set(recent_xy_pos)) <= 2:
                    return True
        return False

    def _break_loop(self) -> None:
        if self.game_engine.verbose > 0:
            print("AI: Detected a loop, breaking.")
        self.current_path = None
        self.loop_breaker_moves_left = 5

    def _get_interrupt_goals(self, log: bool = False) -> List[Goal]:
        interrupt_goals: List[Goal] = []
        if self.game_engine.verbose > 0 and log:
            print("Checking for interrupt goals:")

        for evaluator in [SurvivalEvaluator(), AttackEvaluator(), LootingEvaluator()]:
            goals = evaluator.evaluate(self.game_engine)
            for goal in goals:
                original_score = goal.score
                goal.score *= evaluator.weight
                interrupt_goals.append(goal)
                if self.game_engine.verbose > 0 and log:
                    print(
                        f"  - Interrupt? {evaluator.name}: {goal.name} "
                        f"(raw: {original_score:.2f}, weighted: {goal.score:.2f})"
                    )
        return interrupt_goals

    def _plan_action_for_goal(self, goal: Goal) -> Action:
        player = self.game_engine.player
        if goal.name == "use_health_potion":
            return Action(command=("use", goal.context["item"].name))
        if goal.name == "take_item":
            return Action(command=("take", goal.context["item"].name))
        if goal.name == "attack_monster":
            return Action(command=("attack", goal.context["monster"].name))

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
                if self.game_engine.verbose > 0:
                    print(f"Path found to {target_pos}. Length: {len(path)}")
                self.current_path = path
                return self._follow_path() or Action(command=("look", None))
            elif self.game_engine.verbose > 0:
                print(f"No path found to {target_pos}.")

        return Action(command=self._explore_randomly())

    def _follow_path(self) -> Optional[Action]:
        if not self.current_path:
            return None

        player = self.game_engine.player
        current_pos_xyz = (player.x, player.y, player.current_floor_id)

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
        if self.game_engine.verbose > 0:
            print("Exploring randomly.")
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

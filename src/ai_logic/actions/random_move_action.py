"""
RandomMoveAction - Move randomly when no other options available.

This action mirrors the _explore_randomly() logic from base_state.py,
including loop-breaker behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class RandomMoveAction(AIAction):
    """
    Move randomly when no other options available.

    Used as a fallback and for loop-breaking behavior.

    Utility Scores:
    - 0.99: loop_breaker_active (must break out of loop)
    - 0.10: default fallback action
    """

    @property
    def name(self) -> str:
        return "RandomMove"

    def is_available(self, ctx: "AIContext") -> bool:
        """Always available as a fallback action."""
        return True

    def calculate_utility(self, ctx: "AIContext") -> float:
        """
        High utility when breaking loops, low otherwise.

        Loop breaker mode takes precedence over everything except
        critical survival actions.
        """
        if ctx.loop_breaker_active:
            return 0.99

        return 0.10

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """
        Execute random move, avoiding backtracking and monsters when possible.
        """
        current_ai_map = ctx.get_current_ai_map()
        if not current_ai_map:
            return ("look", None)

        possible_moves: List[Tuple[str, str]] = []
        monster_moves: List[Tuple[str, str]] = []  # Moves that walk into monsters

        for direction, (dx, dy) in [
            ("north", (0, -1)),
            ("south", (0, 1)),
            ("west", (-1, 0)),
            ("east", (1, 0)),
        ]:
            check_x, check_y = ctx.player_x + dx, ctx.player_y + dy
            if current_ai_map.is_valid_move(check_x, check_y):
                tile = current_ai_map.get_tile(check_x, check_y)
                # Avoid walking into monsters during random exploration
                if tile and tile.monster:
                    monster_moves.append(("move", direction))
                else:
                    possible_moves.append(("move", direction))

        # If no safe moves, allow monster moves as last resort (cornered)
        if not possible_moves:
            possible_moves = monster_moves

        if not possible_moves:
            return ("look", None)

        # Try to avoid going back to where we just came from
        opposite_moves = {
            ("move", "north"): ("move", "south"),
            ("move", "south"): ("move", "north"),
            ("move", "east"): ("move", "west"),
            ("move", "west"): ("move", "east"),
        }

        if len(possible_moves) > 1 and ctx.random:
            last_cmd = ai_logic.last_move_command
            if last_cmd:
                # Get the opposite of the last move (which would take us back)
                opposite = opposite_moves.get(last_cmd)
                if opposite and opposite in possible_moves:
                    # Filter out the opposite move to avoid oscillation
                    filtered_moves = [m for m in possible_moves if m != opposite]
                    if filtered_moves:
                        chosen = ctx.random.choice(filtered_moves)
                        ai_logic.last_move_command = chosen
                        return chosen

        # Fallback to choosing any possible move
        if ctx.random:
            chosen = ctx.random.choice(possible_moves)
            ai_logic.last_move_command = chosen
            return chosen
        elif possible_moves:
            ai_logic.last_move_command = possible_moves[0]
            return possible_moves[0]

        return ("look", None)

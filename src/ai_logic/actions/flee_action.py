"""
FleeAction - Flee from adjacent monsters when health is low.

This action mirrors the flee logic from SurvivalState including:
- _get_best_flee_direction()
- _get_safe_moves()
- Threat centroid calculation
- Dead-end avoidance
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class FleeAction(AIAction):
    """
    Flee from adjacent monsters when health is low.

    Utility Score: 0.95 when low health and can flee (not cornered)
    """

    @property
    def name(self) -> str:
        return "Flee"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available if there are adjacent monsters and we're not cornered."""
        return (
            len(ctx.adjacent_monsters) > 0
            and not ctx.is_cornered
            and ctx.is_low_health()
        )

    def calculate_utility(self, ctx: "AIContext") -> float:
        """High utility when low health, adjacent monsters, and can flee."""
        if not self.is_available(ctx):
            return 0.0

        # Only flee when in survival mode (low health)
        if ctx.is_low_health():
            return 0.95

        return 0.0

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """
        Execute flee by moving in the best direction away from threats.

        Prefers directions that:
        1. Maximize distance from threat centroid
        2. Avoid dead ends (prefer more exits)
        """
        # Try intelligent flee direction first
        best_flee = self._get_best_flee_direction(ctx)
        if best_flee:
            message_log.add_message(
                "AI: Low health, fleeing from monster (optimal direction)."
            )
            return best_flee

        # Fall back to any safe move
        safe_moves = self._get_safe_moves(ctx)
        if safe_moves and ctx.random:
            move_command = ctx.random.choice(safe_moves)
            message_log.add_message("AI: Low health, fleeing from monster.")
            return move_command

        return None

    def _get_safe_moves(self, ctx: "AIContext") -> List[Tuple[str, str]]:
        """Get all safe movement options (no walls, no monsters)."""
        safe_moves = []
        possible_moves = {
            "north": (0, -1),
            "south": (0, 1),
            "west": (-1, 0),
            "east": (1, 0),
        }

        current_ai_map = ctx.get_current_ai_map()
        if not current_ai_map:
            return safe_moves

        for move, (dx, dy) in possible_moves.items():
            check_x, check_y = ctx.player_x + dx, ctx.player_y + dy
            tile = current_ai_map.get_tile(check_x, check_y)
            if tile and tile.type != "wall" and not tile.monster:
                safe_moves.append(("move", move))

        return safe_moves

    def _is_safe_move(self, ctx: "AIContext", x: int, y: int) -> bool:
        """Check if a position is safe to move to (not wall, not monster)."""
        current_ai_map = ctx.get_current_ai_map()
        if not current_ai_map:
            return False
        tile = current_ai_map.get_tile(x, y)
        return tile is not None and tile.type != "wall" and not tile.monster

    def _count_exits(self, ctx: "AIContext", x: int, y: int) -> int:
        """Count number of safe exits from a position."""
        exits = 0
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            if self._is_safe_move(ctx, x + dx, y + dy):
                exits += 1
        return exits

    def _get_best_flee_direction(self, ctx: "AIContext") -> Optional[Tuple[str, str]]:
        """Find direction that maximizes distance from threats and avoids dead ends."""
        if not ctx.adjacent_monsters:
            return None

        # Calculate threat center (centroid of all adjacent monsters)
        threat_x = sum(m.x for m in ctx.adjacent_monsters) / len(ctx.adjacent_monsters)
        threat_y = sum(m.y for m in ctx.adjacent_monsters) / len(ctx.adjacent_monsters)

        best_direction = None
        best_score = float("-inf")

        for direction, (dx, dy) in [
            ("north", (0, -1)),
            ("south", (0, 1)),
            ("west", (-1, 0)),
            ("east", (1, 0)),
        ]:
            new_x = ctx.player_x + dx
            new_y = ctx.player_y + dy

            if self._is_safe_move(ctx, new_x, new_y):
                # Calculate distance from threat center (higher is better)
                dist = abs(new_x - threat_x) + abs(new_y - threat_y)

                # Count exits from the new position
                exits = self._count_exits(ctx, new_x, new_y)

                # Penalize dead ends heavily, prefer open areas
                if exits <= 1:
                    exit_bonus = -10  # Avoid dead ends at all costs
                elif exits == 2:
                    exit_bonus = 0  # Corridor or corner, acceptable
                else:
                    exit_bonus = exits  # Open areas are good

                score = dist + exit_bonus

                if score > best_score:
                    best_score = score
                    best_direction = ("move", direction)

        return best_direction

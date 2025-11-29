"""
Path actions for the Utility-Based AI system.

Contains actions for pathing to various targets:
- PathToHealthAction: Path to health potions
- PathToWeaponAction: Path to better weapons
- PathToArmorAction: Path to armor pieces
- PathToQuestAction: Path to quest items
- PathToPortalAction: Path to unvisited portals
- PathToLootAction: Path to other items
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


def apply_distance_modifier(base_utility: float, distance: int) -> float:
    """
    Reduce utility for distant targets, minimum 50% of base.

    This ensures nearby targets of the same priority are preferred.
    """
    decay = max(0.5, 1.0 - (distance / 100.0))
    return base_utility * decay


class PathActionBase(AIAction):
    """Base class for path-finding actions."""

    def _follow_current_path(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Follow the current path if it exists."""
        if not ai_logic.current_path:
            return None

        current_pos_xyz = ctx.player_pos_3d

        # Skip current position if we're already there
        if ai_logic.current_path[0] == current_pos_xyz:
            ai_logic.current_path.pop(0)

        if not ai_logic.current_path:
            ai_logic.current_path = None
            return None

        next_step_xyz = ai_logic.current_path[0]
        move_command = ai_logic._coordinates_to_move_command(
            (current_pos_xyz[0], current_pos_xyz[1]),
            (next_step_xyz[0], next_step_xyz[1]),
        )

        if move_command:
            log_msg = (
                f"AI: Following path. Moving {move_command[1]} to "
                f"({next_step_xyz[0]},{next_step_xyz[1]}) on floor "
                f"{next_step_xyz[2]}."
            )
            message_log.add_message(log_msg)
            ai_logic.last_move_command = move_command
            return move_command

        return None


class PathToHealthAction(PathActionBase):
    """
    Path to nearest health potion.

    Only available when health < 70%.
    Utility Score: 0.70 (base), modified by distance
    """

    @property
    def name(self) -> str:
        return "PathToHealth"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available when health < 70% and health potions are visible."""
        if ctx.health_ratio >= 0.7:
            return False
        if not ctx.target_finder:
            return False

        targets = ctx.target_finder.find_health_potions(
            ctx.player_pos, ctx.player_floor_id
        )
        return len(targets) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """Calculate utility based on health need and distance."""
        if not self.is_available(ctx):
            return 0.0

        if not ctx.target_finder:
            return 0.0

        targets = ctx.target_finder.find_health_potions(
            ctx.player_pos, ctx.player_floor_id
        )
        if not targets:
            return 0.0

        # Get nearest target
        nearest = min(targets, key=lambda t: t[4])  # t[4] is distance
        return apply_distance_modifier(0.70, nearest[4])

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute by pathing to the nearest health potion."""
        if not ctx.target_finder or not ctx.path_finder:
            return None

        targets = ctx.target_finder.find_health_potions(
            ctx.player_pos, ctx.player_floor_id
        )
        if not targets:
            return None

        # Sort by distance
        targets.sort(key=lambda t: t[4])

        # Use risk-aware pathfinding when low health
        for target_x, target_y, target_floor_id, target_type, _ in targets:
            if ctx.health_ratio < 0.7:
                path = ctx.path_finder.find_path_risk_aware(
                    ctx.visible_maps,
                    ctx.player_pos,
                    ctx.player_floor_id,
                    (target_x, target_y),
                    target_floor_id,
                    player_health_ratio=ctx.health_ratio,
                    require_explored=True,
                )
            else:
                path = ctx.path_finder.find_path_bfs(
                    ctx.visible_maps,
                    ctx.player_pos,
                    ctx.player_floor_id,
                    (target_x, target_y),
                    target_floor_id,
                    require_explored=True,
                )

            if path:
                message_log.add_message(
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) "
                    f"on floor {target_floor_id}."
                )
                ai_logic.current_path = path
                return self._follow_current_path(ctx, ai_logic, message_log)

        return None


class PathToWeaponAction(PathActionBase):
    """
    Path to better weapon.

    Utility Score: 0.65 (base), modified by distance
    """

    @property
    def name(self) -> str:
        return "PathToWeapon"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available when better weapons are visible."""
        if not ctx.target_finder:
            return False
        targets = ctx.target_finder.find_weapons(ctx.player_pos, ctx.player_floor_id)
        return len(targets) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """Calculate utility based on distance."""
        if not self.is_available(ctx):
            return 0.0

        if not ctx.target_finder:
            return 0.0

        targets = ctx.target_finder.find_weapons(ctx.player_pos, ctx.player_floor_id)
        if not targets:
            return 0.0

        nearest = min(targets, key=lambda t: t[4])
        return apply_distance_modifier(0.65, nearest[4])

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute by pathing to the nearest better weapon."""
        if not ctx.target_finder or not ctx.path_finder:
            return None

        targets = ctx.target_finder.find_weapons(ctx.player_pos, ctx.player_floor_id)
        if not targets:
            return None

        targets.sort(key=lambda t: t[4])

        for target_x, target_y, target_floor_id, target_type, _ in targets:
            path = ctx.path_finder.find_path_bfs(
                ctx.visible_maps,
                ctx.player_pos,
                ctx.player_floor_id,
                (target_x, target_y),
                target_floor_id,
                require_explored=True,
            )

            if path:
                message_log.add_message(
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) "
                    f"on floor {target_floor_id}."
                )
                ai_logic.current_path = path
                return self._follow_current_path(ctx, ai_logic, message_log)

        return None


class PathToArmorAction(PathActionBase):
    """
    Path to armor pieces (for empty slots or better armor).

    Utility Score: 0.60 (base), modified by distance
    """

    @property
    def name(self) -> str:
        return "PathToArmor"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available when armor is visible."""
        if not ctx.target_finder:
            return False
        targets = ctx.target_finder.find_armor(ctx.player_pos, ctx.player_floor_id)
        return len(targets) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """Calculate utility based on distance."""
        if not self.is_available(ctx):
            return 0.0

        if not ctx.target_finder:
            return 0.0

        targets = ctx.target_finder.find_armor(ctx.player_pos, ctx.player_floor_id)
        if not targets:
            return 0.0

        nearest = min(targets, key=lambda t: t[4])
        return apply_distance_modifier(0.60, nearest[4])

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute by pathing to the nearest armor piece."""
        if not ctx.target_finder or not ctx.path_finder:
            return None

        targets = ctx.target_finder.find_armor(ctx.player_pos, ctx.player_floor_id)
        if not targets:
            return None

        targets.sort(key=lambda t: t[4])

        for target_x, target_y, target_floor_id, target_type, _ in targets:
            path = ctx.path_finder.find_path_bfs(
                ctx.visible_maps,
                ctx.player_pos,
                ctx.player_floor_id,
                (target_x, target_y),
                target_floor_id,
                require_explored=True,
            )

            if path:
                message_log.add_message(
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) "
                    f"on floor {target_floor_id}."
                )
                ai_logic.current_path = path
                return self._follow_current_path(ctx, ai_logic, message_log)

        return None


class PathToQuestAction(PathActionBase):
    """
    Path to quest items.

    Uses risk-aware pathfinding when health < 70%.
    Utility Score: 0.55 (base), modified by distance
    """

    @property
    def name(self) -> str:
        return "PathToQuest"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available when quest items are visible."""
        if not ctx.target_finder:
            return False
        targets = ctx.target_finder.find_quest_items(
            ctx.player_pos, ctx.player_floor_id, same_floor_only=False
        )
        return len(targets) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """Calculate utility based on distance."""
        if not self.is_available(ctx):
            return 0.0

        if not ctx.target_finder:
            return 0.0

        targets = ctx.target_finder.find_quest_items(
            ctx.player_pos, ctx.player_floor_id, same_floor_only=False
        )
        if not targets:
            return 0.0

        nearest = min(targets, key=lambda t: t[4])
        return apply_distance_modifier(0.55, nearest[4])

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute by pathing to the nearest quest item."""
        if not ctx.target_finder or not ctx.path_finder:
            return None

        targets = ctx.target_finder.find_quest_items(
            ctx.player_pos, ctx.player_floor_id, same_floor_only=False
        )
        if not targets:
            return None

        targets.sort(key=lambda t: t[4])

        for target_x, target_y, target_floor_id, target_type, _ in targets:
            # Use risk-aware pathfinding when health is below 70%
            if ctx.health_ratio < 0.7:
                path = ctx.path_finder.find_path_risk_aware(
                    ctx.visible_maps,
                    ctx.player_pos,
                    ctx.player_floor_id,
                    (target_x, target_y),
                    target_floor_id,
                    player_health_ratio=ctx.health_ratio,
                    require_explored=True,
                )
            else:
                path = ctx.path_finder.find_path_bfs(
                    ctx.visible_maps,
                    ctx.player_pos,
                    ctx.player_floor_id,
                    (target_x, target_y),
                    target_floor_id,
                    require_explored=True,
                )

            if path:
                message_log.add_message(
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) "
                    f"on floor {target_floor_id}."
                )
                ai_logic.current_path = path
                return self._follow_current_path(ctx, ai_logic, message_log)

        return None


class PathToPortalAction(PathActionBase):
    """
    Path to unvisited portals or portals to unexplored floors.

    Utility Score: 0.45-0.55 (base), modified by distance and floor exploration status.
    Higher utility when current floor is mostly explored.
    """

    @property
    def name(self) -> str:
        return "PathToPortal"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available when unvisited portals exist."""
        if not ctx.explorer:
            return False

        unvisited = ctx.explorer.find_unvisited_portals(
            ctx.player_pos, ctx.player_floor_id
        )
        portal_to_unexplored = ctx.explorer.find_portal_to_unexplored_floor(
            ctx.player_pos, ctx.player_floor_id
        )
        return len(unvisited) > 0 or len(portal_to_unexplored) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """
        Calculate utility based on distance and floor exploration status.

        Base utility is 0.45, but increases to 0.55 when current floor is
        >80% explored to encourage cross-floor progression.
        """
        if not self.is_available(ctx):
            return 0.0

        if not ctx.explorer:
            return 0.0

        # Combine both portal types and find nearest
        targets: List[Tuple[int, int, int, str, int]] = []
        targets.extend(
            ctx.explorer.find_unvisited_portals(ctx.player_pos, ctx.player_floor_id)
        )
        targets.extend(
            ctx.explorer.find_portal_to_unexplored_floor(
                ctx.player_pos, ctx.player_floor_id
            )
        )

        if not targets:
            return 0.0

        # Higher base utility if current floor is mostly explored
        exploration_ratio = ctx.explorer.get_floor_exploration_ratio(
            ctx.player_floor_id
        )
        if exploration_ratio > 0.8:
            base_utility = 0.55  # Prioritize portal usage when floor is mostly done
        else:
            base_utility = 0.45

        nearest = min(targets, key=lambda t: t[4])
        return apply_distance_modifier(base_utility, nearest[4])

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute by pathing to the nearest portal."""
        if not ctx.explorer or not ctx.path_finder:
            return None

        # Combine both portal types
        targets: List[Tuple[int, int, int, str, int]] = []
        targets.extend(
            ctx.explorer.find_unvisited_portals(ctx.player_pos, ctx.player_floor_id)
        )
        targets.extend(
            ctx.explorer.find_portal_to_unexplored_floor(
                ctx.player_pos, ctx.player_floor_id
            )
        )

        if not targets:
            return None

        # Sort by priority (portal_to_unexplored first) then distance
        def sort_key(t: Tuple[int, int, int, str, int]) -> Tuple[int, int]:
            priority = 0 if t[3] == "portal_to_unexplored" else 1
            return (priority, t[4])

        targets.sort(key=sort_key)

        for target_x, target_y, target_floor_id, target_type, _ in targets:
            path = ctx.path_finder.find_path_bfs(
                ctx.visible_maps,
                ctx.player_pos,
                ctx.player_floor_id,
                (target_x, target_y),
                target_floor_id,
                require_explored=True,
            )

            if path:
                message_log.add_message(
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) "
                    f"on floor {target_floor_id}."
                )
                ai_logic.current_path = path
                return self._follow_current_path(ctx, ai_logic, message_log)

        return None


class PathToLootAction(PathActionBase):
    """
    Path to other items (miscellaneous loot).

    Utility Score: 0.40 (base), modified by distance
    """

    @property
    def name(self) -> str:
        return "PathToLoot"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available when other items are visible."""
        if not ctx.target_finder:
            return False
        targets = ctx.target_finder.find_other_items(
            ctx.player_pos, ctx.player_floor_id
        )
        return len(targets) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """Calculate utility based on distance."""
        if not self.is_available(ctx):
            return 0.0

        if not ctx.target_finder:
            return 0.0

        targets = ctx.target_finder.find_other_items(
            ctx.player_pos, ctx.player_floor_id
        )
        if not targets:
            return 0.0

        nearest = min(targets, key=lambda t: t[4])
        return apply_distance_modifier(0.40, nearest[4])

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute by pathing to the nearest item."""
        if not ctx.target_finder or not ctx.path_finder:
            return None

        targets = ctx.target_finder.find_other_items(
            ctx.player_pos, ctx.player_floor_id
        )
        if not targets:
            return None

        targets.sort(key=lambda t: t[4])

        for target_x, target_y, target_floor_id, target_type, _ in targets:
            path = ctx.path_finder.find_path_bfs(
                ctx.visible_maps,
                ctx.player_pos,
                ctx.player_floor_id,
                (target_x, target_y),
                target_floor_id,
                require_explored=True,
            )

            if path:
                message_log.add_message(
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) "
                    f"on floor {target_floor_id}."
                )
                ai_logic.current_path = path
                return self._follow_current_path(ctx, ai_logic, message_log)

        return None

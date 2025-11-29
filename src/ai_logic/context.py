"""
AIContext - Immutable snapshot of game state for utility calculation.

This module provides the AIContext dataclass which replaces direct access
to AILogic in action classes, making them pure functions of state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from random import Random

    from src.items import Item
    from src.map_algorithms.pathfinding import PathFinder
    from src.world_map import WorldMap

    from .ai_monster_view import AIMonsterView
    from .bestiary import Bestiary
    from .explorer import Explorer
    from .target_finder import TargetFinder


@dataclass
class AIContext:
    """
    Immutable snapshot of game state for utility calculation.

    This replaces direct access to AILogic in action classes,
    making them pure functions of state.

    All fields are read-only and should not be modified after creation.
    The context is rebuilt each turn from the current game state.
    """

    # Player state
    player_x: int
    player_y: int
    player_floor_id: int
    player_health: int
    player_max_health: int
    player_attack: int
    player_defense: int

    # Pre-computed flags (from AILogic methods)
    health_ratio: float
    survival_threshold: float
    is_cornered: bool
    is_in_loop: bool
    loop_breaker_active: bool

    # Adjacent monsters (AIMonsterView list - name and position only)
    adjacent_monsters: List["AIMonsterView"]

    # Current tile state
    current_tile_has_item: bool
    current_tile_item_name: Optional[str]
    current_tile_item: Optional["Item"]

    # Inventory summary
    inventory_items: List["Item"]
    has_healing_item: bool
    has_fire_potion: bool

    # Equipment state (slot -> Item or None)
    equipped_items: Dict[str, Optional["Item"]]

    # Pathfinding state
    current_path: Optional[List[Tuple[int, int, int]]]

    # References for complex calculations (read-only access)
    visible_maps: Dict[int, "WorldMap"]
    path_finder: Optional["PathFinder"]
    bestiary: Optional["Bestiary"]
    explorer: Optional["Explorer"]
    target_finder: Optional["TargetFinder"]
    random: Optional["Random"]

    @property
    def player_pos(self) -> Tuple[int, int]:
        """Return player position as (x, y) tuple."""
        return (self.player_x, self.player_y)

    @property
    def player_pos_3d(self) -> Tuple[int, int, int]:
        """Return player position as (x, y, floor_id) tuple."""
        return (self.player_x, self.player_y, self.player_floor_id)

    def get_current_ai_map(self) -> Optional["WorldMap"]:
        """Get the AI visible map for the current floor."""
        return self.visible_maps.get(self.player_floor_id)

    def is_low_health(self) -> bool:
        """Check if player health is below survival threshold."""
        return self.health_ratio <= self.survival_threshold

    def has_adjacent_monsters(self) -> bool:
        """Check if there are monsters adjacent to the player."""
        return len(self.adjacent_monsters) > 0

    def current_tile_has_quest_item(self) -> bool:
        """Check if the item on the current tile is a quest item."""
        if not self.current_tile_item:
            return False
        from src.items import QuestItem

        return isinstance(self.current_tile_item, QuestItem)

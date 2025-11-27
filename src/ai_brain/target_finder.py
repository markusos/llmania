from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Tuple

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.items import Item


class TargetFinder:
    """
    Scans the map to find various points of interest for the AI.
    """

    def __init__(self, game_engine: "GameEngine"):
        self.game_engine = game_engine
        self.player = game_engine.player
        self.ai_visible_maps = game_engine.visible_maps

    def _find_items(
        self,
        item_filter: Callable[[Item], bool],
        target_type: str,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        """
        A generic helper to find items based on a filter.
        """
        targets = []
        player_pos_xy = (self.player.x, self.player.y)
        player_floor_id = self.player.current_floor_id

        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            if same_floor_only and floor_id != player_floor_id:
                continue

            for y, x in ai_map.iter_coords():
                tile = ai_map.get_tile(x, y)
                if tile and tile.is_explored and tile.item and item_filter(tile.item):
                    # Estimate distance considering floor changes
                    dist_est = (
                        abs(x - player_pos_xy[0])
                        + abs(y - player_pos_xy[1])
                        + abs(floor_id - player_floor_id) * 10
                    )
                    targets.append((x, y, floor_id, target_type, dist_est))
        return targets

    def find_health_potions(
        self, same_floor_only: bool = False
    ) -> List[Tuple[int, int, int, str, int]]:
        """
        Finds health potions, typically when the player is at low health.
        """
        from src.effects import HealingEffect
        from src.items import ConsumableItem

        def item_filter(item: "Item") -> bool:
            if not isinstance(item, ConsumableItem):
                return False
            return any(isinstance(e, HealingEffect) for e in item.effects)

        return self._find_items(item_filter, "health_potion", same_floor_only)

    def find_other_items(
        self, same_floor_only: bool = False
    ) -> List[Tuple[int, int, int, str, int]]:
        """
        Finds any items that are not health potions.
        """
        from src.effects import HealingEffect
        from src.items import ConsumableItem

        def item_filter(item: "Item") -> bool:
            if isinstance(item, ConsumableItem):
                # Exclude health potions from this search
                return not any(isinstance(e, HealingEffect) for e in item.effects)
            return True

        return self._find_items(item_filter, "other_item", same_floor_only)

    def find_monsters(self) -> List[Tuple[int, int, int, str, int]]:
        """
        Finds all monsters that are not adjacent to the player.
        """
        targets = []
        player_pos_xy = (self.player.x, self.player.y)
        player_floor_id = self.player.current_floor_id

        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            for y, x in ai_map.iter_coords():
                tile = ai_map.get_tile(x, y)
                if tile and tile.is_explored and tile.monster:
                    is_adjacent = False
                    if floor_id == player_floor_id:
                        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                            if (
                                player_pos_xy[0] + dx == x
                                and player_pos_xy[1] + dy == y
                            ):
                                is_adjacent = True
                                break
                    if not is_adjacent:
                        dist_est = (
                            abs(x - player_pos_xy[0])
                            + abs(y - player_pos_xy[1])
                            + abs(floor_id - player_floor_id) * 10
                        )
                        targets.append((x, y, floor_id, "monster", dist_est))
        return targets

    def find_player(self) -> Tuple[int, int, int]:
        """
        Returns the player's current position and floor.
        """
        return (self.player.x, self.player.y, self.player.current_floor_id)

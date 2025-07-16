from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

if TYPE_CHECKING:
    from src.item import Item
    from src.player import Player
    from src.world_map import WorldMap


class TargetFinder:
    def __init__(self, player: "Player", ai_visible_maps: Dict[int, "WorldMap"]):
        self.player = player
        self.ai_visible_maps = ai_visible_maps

    def _find_items(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        item_filter: Callable[["Item"], bool],
        target_type: str,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        targets = []
        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            if same_floor_only and floor_id != player_floor_id:
                continue
            for y, x in ai_map.iter_coords():
                tile = ai_map.get_tile(x, y)
                if tile and tile.is_explored and tile.item and item_filter(tile.item):
                    dist_est = (
                        abs(x - player_pos_xy[0])
                        + abs(y - player_pos_xy[1])
                        + abs(floor_id - player_floor_id) * 10
                    )
                    targets.append((x, y, floor_id, target_type, dist_est))
        return targets

    def find_quest_items(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        return self._find_items(
            player_pos_xy,
            player_floor_id,
            lambda item: item.properties.get("type") == "quest",
            "quest_item",
            same_floor_only,
        )

    def find_health_potions(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        low_health_threshold = self.player.max_health * 0.5
        if self.player.health >= low_health_threshold:
            return []

        return self._find_items(
            player_pos_xy,
            player_floor_id,
            lambda item: "health potion" in item.name.lower()
            and item.properties.get("type") == "heal",
            "health_potion",
            same_floor_only,
        )

    def find_other_items(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        def item_filter(item: "Item") -> bool:
            is_potion_full_health = (
                item.properties.get("type") == "heal"
                and "health potion" in item.name.lower()
                and self.player.health >= self.player.max_health
            )
            is_quest_item = item.properties.get("type") == "quest"
            return not (is_potion_full_health or is_quest_item)

        return self._find_items(
            player_pos_xy, player_floor_id, item_filter, "other_item", same_floor_only
        )

    def find_monsters(
        self, player_pos_xy: Tuple[int, int], player_floor_id: int
    ) -> List[Tuple[int, int, int, str, int]]:
        targets = []
        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            for y_monster in range(ai_map.height):
                for x_monster in range(ai_map.width):
                    tile = ai_map.get_tile(x_monster, y_monster)
                    if tile and tile.is_explored and tile.monster:
                        is_adjacent = False
                        if floor_id == player_floor_id:
                            for dx_adj, dy_adj in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                                if (
                                    player_pos_xy[0] + dx_adj == x_monster
                                    and player_pos_xy[1] + dy_adj == y_monster
                                ):
                                    is_adjacent = True
                                    break
                        if not is_adjacent:
                            dist_est = (
                                abs(x_monster - player_pos_xy[0])
                                + abs(y_monster - player_pos_xy[1])
                                + abs(floor_id - player_floor_id) * 10
                            )
                            targets.append(
                                (x_monster, y_monster, floor_id, "monster", dist_est)
                            )
        return targets

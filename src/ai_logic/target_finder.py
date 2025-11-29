from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

if TYPE_CHECKING:
    from src.items import Item
    from src.world_map import WorldMap

    from .ai_player_view import AIPlayerView


class TargetFinder:
    def __init__(
        self, player_view: "AIPlayerView", ai_visible_maps: Dict[int, "WorldMap"]
    ):
        self.player_view = player_view
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
        from src.items import QuestItem

        return self._find_items(
            player_pos_xy,
            player_floor_id,
            lambda item: isinstance(item, QuestItem),
            "quest_item",
            same_floor_only,
        )

    def find_health_potions(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        """Find health potions on the map."""
        from src.effects import HealingEffect
        from src.items import ConsumableItem

        def item_filter(item: "Item") -> bool:
            if not isinstance(item, ConsumableItem):
                return False
            return any(isinstance(e, HealingEffect) for e in item.effects)

        return self._find_items(
            player_pos_xy,
            player_floor_id,
            item_filter,
            "health_potion",
            same_floor_only,
        )

    def find_weapons(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        """Find weapons that are better than currently equipped."""
        from src.items import EquippableItem

        current_attack_bonus = 0
        equipped_main_hand = self.player_view.get_equipped_item("main_hand")
        if equipped_main_hand:
            current_attack_bonus = equipped_main_hand.properties.get("attack_bonus", 0)

        def item_filter(item: "Item") -> bool:
            if not isinstance(item, EquippableItem):
                return False
            if item.properties.get("slot") != "main_hand":
                return False
            # Only target weapons better than what we have
            item_attack_bonus = item.properties.get("attack_bonus", 0)
            return item_attack_bonus > current_attack_bonus

        return self._find_items(
            player_pos_xy,
            player_floor_id,
            item_filter,
            "weapon",
            same_floor_only,
        )

    def find_armor(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        """Find armor pieces for empty slots or better than equipped."""
        from src.items import EquippableItem

        armor_slots = ["head", "chest", "legs", "off_hand", "boots"]

        def item_filter(item: "Item") -> bool:
            if not isinstance(item, EquippableItem):
                return False
            slot = item.properties.get("slot")
            if slot not in armor_slots:
                return False
            # Check if slot is empty or item is better
            equipped = self.player_view.get_equipped_item(slot)
            if equipped is None:
                return True
            # Compare defense bonus
            current_defense = equipped.properties.get("defense_bonus", 0)
            item_defense = item.properties.get("defense_bonus", 0)
            return item_defense > current_defense

        return self._find_items(
            player_pos_xy,
            player_floor_id,
            item_filter,
            "armor",
            same_floor_only,
        )

    def find_other_items(
        self,
        player_pos_xy: Tuple[int, int],
        player_floor_id: int,
        same_floor_only: bool = False,
    ) -> List[Tuple[int, int, int, str, int]]:
        """Find items not covered by other find methods (excludes weapons, armor,
        health potions, and quest items)."""
        from src.effects import HealingEffect
        from src.items import ConsumableItem, EquippableItem, QuestItem

        def item_filter(item: "Item") -> bool:
            # Exclude quest items (handled by find_quest_items)
            if isinstance(item, QuestItem):
                return False
            # Exclude equippable items (handled by find_weapons/find_armor)
            if isinstance(item, EquippableItem):
                return False
            # Exclude health potions (handled by find_health_potions)
            if isinstance(item, ConsumableItem) and any(
                isinstance(e, HealingEffect) for e in item.effects
            ):
                return False
            return True

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

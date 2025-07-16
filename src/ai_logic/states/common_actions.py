from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

if TYPE_CHECKING:
    from src.ai_logic.main import AILogic


def use_item(ai_logic: "AILogic", item_type: str) -> Optional[Tuple[str, str]]:
    if item_type == "heal":
        # Do not use healing items if health is full
        if ai_logic.player.health >= ai_logic.player.max_health:
            return None
    for item in ai_logic.player.inventory:
        if item.properties.get("type") == item_type:
            ai_logic.message_log.add_message(f"AI: Using {item.name}.")
            return ("use", item.name)
    return None


def equip_better_weapon(ai_logic: "AILogic") -> Optional[Tuple[str, str]]:
    for item in ai_logic.player.inventory:
        if item.properties.get("type") == "weapon":
            current_attack_bonus = 0
            if ai_logic.player.equipped_weapon:
                current_attack_bonus = ai_logic.player.equipped_weapon.properties.get(
                    "attack_bonus", 0
                )

            new_weapon_attack_bonus = item.properties.get("attack_bonus", 0)
            if new_weapon_attack_bonus > current_attack_bonus:
                ai_logic.message_log.add_message(
                    f"AI: Equipping better weapon {item.name}."
                )
                return ("use", item.name)
    return None


def pickup_item(ai_logic: "AILogic") -> Optional[Tuple[str, str]]:
    player = ai_logic.player
    current_ai_map = ai_logic.ai_visible_maps.get(player.current_floor_id)
    if current_ai_map:
        current_tile = current_ai_map.get_tile(player.x, player.y)
        if current_tile and current_tile.item:
            item_name = current_tile.item.name
            ai_logic.message_log.add_message(
                f"AI: Found item {item_name} on current tile, taking it."
            )
            ai_logic.current_path = None
            return ("take", item_name)
    return None


def path_to_best_target(
    ai_logic: "AILogic",
    target_finder_func: Callable[
        [Tuple[int, int], int], List[Tuple[int, int, int, str, int]]
    ],
    sort_key_func: Optional[
        Callable[[Tuple[int, int, int, str, int]], Tuple[int, int]]
    ] = None,
) -> Optional[Tuple[str, Optional[str]]]:
    player_pos_xy = (ai_logic.player.x, ai_logic.player.y)
    player_floor_id = ai_logic.player.current_floor_id

    targets = target_finder_func(player_pos_xy, player_floor_id)
    if sort_key_func:
        targets.sort(key=sort_key_func)

    for target_x, target_y, target_floor_id, target_type, _ in targets:
        avoid_monsters = ai_logic.state.__class__.__name__ == "SurvivalState"
        path = ai_logic.path_finder.find_path_bfs(
            ai_logic.ai_visible_maps,
            player_pos_xy,
            player_floor_id,
            (target_x, target_y),
            target_floor_id,
            avoid_monsters=avoid_monsters,
        )
        if path:
            log_msg = (
                f"AI: Pathing to {target_type} at ({target_x},{target_y}) on "
                f"floor {target_floor_id}."
            )
            ai_logic.message_log.add_message(log_msg)
            ai_logic.current_path = path
            return ai_logic.state._follow_path()
    return None

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

if TYPE_CHECKING:
    from src.ai_logic.main import AILogic


def use_item(ai_logic: "AILogic", item_type: str) -> Optional[Tuple[str, str]]:
    if item_type == "heal":
        # Do not use healing items if health is full
        if ai_logic.player_view.health >= ai_logic.player_view.max_health:
            return None
    for item in ai_logic.player_view.inventory_items:
        if item.properties.get("type") == item_type:
            ai_logic.message_log.add_message(f"AI: Using {item.name}.")
            return ("use", item.name)
    return None


def equip_better_weapon(ai_logic: "AILogic") -> Optional[Tuple[str, str]]:
    for item in ai_logic.player_view.inventory_items:
        if item.properties.get("type") == "weapon":
            current_attack_bonus = 0
            equipped_main_hand = ai_logic.player_view.get_equipped_item("main_hand")
            if equipped_main_hand:
                current_attack_bonus = equipped_main_hand.properties.get(
                    "attack_bonus", 0
                )

            new_weapon_attack_bonus = item.properties.get("attack_bonus", 0)
            if new_weapon_attack_bonus > current_attack_bonus:
                ai_logic.message_log.add_message(
                    f"AI: Equipping better weapon {item.name}."
                )
                return ("use", item.name)
    return None


def equip_beneficial_items(ai_logic: "AILogic") -> Optional[Tuple[str, str]]:
    """
    Equip armor and better weapons automatically.

    Checks inventory for:
    1. Better weapons (higher attack bonus)
    2. Armor for empty slots
    3. Better armor than currently equipped

    Returns the first equip action found, or None if nothing to equip.
    """
    from src.items import EquippableItem

    armor_slots = ["head", "chest", "legs", "off_hand", "boots"]

    for item in ai_logic.player_view.inventory_items:
        if not isinstance(item, EquippableItem):
            continue

        slot = item.properties.get("slot")
        if not slot:
            continue

        equipped = ai_logic.player_view.get_equipped_item(slot)

        # Handle weapons (main_hand)
        if slot == "main_hand":
            current_attack = 0
            if equipped:
                current_attack = equipped.properties.get("attack_bonus", 0)
            item_attack = item.properties.get("attack_bonus", 0)
            if item_attack > current_attack:
                ai_logic.message_log.add_message(
                    f"AI: Equipping better weapon {item.name}."
                )
                return ("use", item.name)

        # Handle armor slots
        elif slot in armor_slots:
            if equipped is None:
                # Empty slot - equip immediately
                ai_logic.message_log.add_message(
                    f"AI: Equipping {item.name} to empty {slot} slot."
                )
                return ("use", item.name)
            else:
                # Compare defense bonus
                current_defense = equipped.properties.get("defense_bonus", 0)
                item_defense = item.properties.get("defense_bonus", 0)
                if item_defense > current_defense:
                    ai_logic.message_log.add_message(
                        f"AI: Equipping better armor {item.name}."
                    )
                    return ("use", item.name)

    return None


def pickup_item(ai_logic: "AILogic") -> Optional[Tuple[str, str]]:
    player_view = ai_logic.player_view
    current_ai_map = ai_logic.ai_visible_maps.get(player_view.current_floor_id)
    if current_ai_map:
        current_tile = current_ai_map.get_tile(player_view.x, player_view.y)
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
    player_pos_xy = (ai_logic.player_view.x, ai_logic.player_view.y)
    player_floor_id = ai_logic.player_view.current_floor_id

    targets = target_finder_func(player_pos_xy, player_floor_id)
    if sort_key_func:
        targets.sort(key=sort_key_func)

    is_survival_mode = ai_logic.state.__class__.__name__ == "SurvivalState"
    health_ratio = ai_logic.player_view.health / ai_logic.player_view.max_health

    for target_x, target_y, target_floor_id, target_type, _ in targets:
        if is_survival_mode:
            # Use risk-aware pathfinding that avoids monster-adjacent tiles
            path = ai_logic.path_finder.find_path_risk_aware(
                ai_logic.ai_visible_maps,
                player_pos_xy,
                player_floor_id,
                (target_x, target_y),
                target_floor_id,
                player_health_ratio=health_ratio,
                require_explored=True,
            )
        else:
            path = ai_logic.path_finder.find_path_bfs(
                ai_logic.ai_visible_maps,
                player_pos_xy,
                player_floor_id,
                (target_x, target_y),
                target_floor_id,
                avoid_monsters=False,
                require_explored=True,
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

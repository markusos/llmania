from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_state import AIState

if TYPE_CHECKING:
    pass


class LootingState(AIState):
    def handle_transitions(self) -> str:
        player = self.ai_logic.player
        if player.health <= player.max_health / 2:
            return "SurvivalState"
        if self.ai_logic._get_adjacent_monsters():
            return "AttackingState"
        return "LootingState"

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        player = self.ai_logic.player
        player_pos_xy = (player.x, player.y)
        player_floor_id = player.current_floor_id

        # 1. Use health potions if low on health
        if player.health <= player.max_health / 2:
            for item in player.inventory:
                if item.properties.get("type") == "heal":
                    self.ai_logic.message_log.add_message(
                        f"AI: Low health, using {item.name}."
                    )
                    return ("use", item.name)

        # 2. Equip better weapons
        for item in player.inventory:
            if item.properties.get("type") == "weapon":
                current_attack_bonus = (
                    player.equipped_weapon.properties.get("attack_bonus", 0)
                    if player.equipped_weapon
                    else 0
                )
                new_weapon_attack_bonus = item.properties.get("attack_bonus", 0)
                if new_weapon_attack_bonus > current_attack_bonus:
                    self.ai_logic.message_log.add_message(
                        f"AI: Equipping better weapon {item.name}."
                    )
                    return ("use", item.name)

        # 3. Take item on current tile
        current_ai_map = self.ai_logic.ai_visible_maps.get(player_floor_id)
        if current_ai_map:
            current_tile = current_ai_map.get_tile(player.x, player.y)
            if current_tile and current_tile.item:
                item_name = current_tile.item.name
                self.ai_logic.message_log.add_message(
                    f"AI: Found item {item_name} on current tile, taking it."
                )
                self.ai_logic.current_path = None
                return ("take", item_name)

        # 4. Pathfind to other known items
        other_items = self.ai_logic.target_finder.find_other_items(
            player_pos_xy, player_floor_id
        )
        if other_items:
            target_x, target_y, target_floor_id, _, _ = other_items[0]
            path = self.ai_logic.path_finder.find_path_bfs(
                self.ai_logic.ai_visible_maps,
                player_pos_xy,
                player_floor_id,
                (target_x, target_y),
                target_floor_id,
            )
            if path:
                log_msg = f"AI: Pathing to item at ({target_x},{target_y}) "
                log_msg += f"on floor {target_floor_id}."
                self.ai_logic.message_log.add_message(log_msg)
                self.ai_logic.current_path = path
                return self._follow_path()

        # 5. If no items to loot, switch back to exploring
        self.ai_logic.state = self.ai_logic._get_state("ExploringState")
        return self.ai_logic.state.get_next_action()

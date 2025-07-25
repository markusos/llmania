from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_state import AIState

if TYPE_CHECKING:
    pass


class ExploringState(AIState):
    def handle_transitions(self) -> str:
        player = self.ai_logic.player
        if player.health <= player.max_health / 2:
            return "SurvivalState"
        if self.ai_logic._get_adjacent_monsters():
            return "AttackingState"
        current_ai_map = self.ai_logic.ai_visible_maps.get(player.current_floor_id)
        if current_ai_map:
            current_tile = current_ai_map.get_tile(player.x, player.y)
            if current_tile and current_tile.item:
                return "LootingState"
        return "ExploringState"

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        self.ai_logic.current_path = None
        player_pos_xy = (self.ai_logic.player.x, self.ai_logic.player.y)
        player_floor_id = self.ai_logic.player.current_floor_id

        # 1. Exploration
        exploration_path = self.ai_logic.explorer.find_exploration_targets(
            player_pos_xy, player_floor_id
        )
        if exploration_path:
            self.ai_logic.current_path = exploration_path
            target_coord = self.ai_logic.current_path[-1]
            log_msg = (
                f"AI: Pathing to explore at ({target_coord[0]},"
                f"{target_coord[1]}) on floor {target_coord[2]}."
            )
            self.ai_logic.message_log.add_message(log_msg)
            return self._follow_path()

        # 2. Path to the most important target
        action = self._path_to_best_target(
            self._find_best_target, self._target_sort_key
        )
        if action:
            return action

        # 3. If no other options, explore randomly
        self.ai_logic.message_log.add_message(
            "AI: No path found for any target or exploration."
        )
        return self._explore_randomly()

    def _find_best_target(self, player_pos_xy, player_floor_id):
        targets = []
        # 1. Survival: Find health potions if low on health
        if self.ai_logic.player.health <= self.ai_logic.player.max_health / 2:
            targets.extend(
                self.ai_logic.target_finder.find_health_potions(
                    player_pos_xy, player_floor_id
                )
            )
        # 2. Quest Items
        targets.extend(
            self.ai_logic.target_finder.find_quest_items(player_pos_xy, player_floor_id)
        )
        # 3. Other targets
        targets.extend(
            self.ai_logic.explorer.find_unvisited_portals(
                player_pos_xy, player_floor_id
            )
        )
        targets.extend(
            self.ai_logic.explorer.find_portal_to_unexplored_floor(
                player_pos_xy, player_floor_id
            )
        )
        targets.extend(
            self.ai_logic.target_finder.find_other_items(player_pos_xy, player_floor_id)
        )
        targets.extend(
            self.ai_logic.target_finder.find_monsters(player_pos_xy, player_floor_id)
        )
        return targets

    def _target_sort_key(self, target_data):
        _, _, _, target_type, dist = target_data
        priority = 6
        if target_type == "quest_item":
            priority = 1
        elif target_type == "unvisited_portal":
            priority = 2
        elif target_type == "portal_to_unexplored":
            priority = 3
        elif target_type == "health_potion":
            priority = 4
        elif target_type == "monster":
            priority = 5
        return (priority, dist)

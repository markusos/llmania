from __future__ import annotations

from typing import Optional, Tuple

from .base_state import AIState


class ExploringState(AIState):
    def handle_transitions(self) -> str:
        player_view = self.ai_logic.player_view
        # Use dynamic survival threshold
        if self.ai_logic.should_enter_survival_mode():
            return "SurvivalState"
        if self.ai_logic._get_adjacent_monsters():
            # Always transition to attacking when monsters are adjacent
            # AttackingState will handle the combat evaluation
            return "AttackingState"
        current_ai_map = self.ai_logic.ai_visible_maps.get(player_view.current_floor_id)
        if current_ai_map:
            current_tile = current_ai_map.get_tile(player_view.x, player_view.y)
            if current_tile and current_tile.item:
                return "LootingState"
        return "ExploringState"

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        player_pos_xy = (self.ai_logic.player_view.x, self.ai_logic.player_view.y)
        player_floor_id = self.ai_logic.player_view.current_floor_id

        # Equip any beneficial items in inventory
        action = self._equip_beneficial_items()
        if action:
            return action

        # 1. If we have an existing path, follow it
        if self.ai_logic.current_path:
            path_action = self._follow_path()
            if path_action:
                return path_action
            # Path exhausted or invalid, clear it
            self.ai_logic.current_path = None

        # Check for optimal quest route across floors
        quest_route = self.ai_logic.calculate_optimal_quest_route()
        if quest_route and len(quest_route) > 1:
            self.ai_logic.current_path = quest_route
            target_coord = quest_route[-1]
            self.ai_logic.message_log.add_message(
                f"AI: Calculated optimal route to quest item at "
                f"({target_coord[0]},{target_coord[1]}) on floor {target_coord[2]}."
            )
            return self._follow_path()

        # 2. Find exploration targets
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
        # Health Potions (if health < 70%)
        health_threshold = self.ai_logic.player_view.max_health * 0.7
        if self.ai_logic.player_view.health < health_threshold:
            targets.extend(
                self.ai_logic.target_finder.find_health_potions(
                    player_pos_xy, player_floor_id
                )
            )
        # 2. Weapons (if better than current)
        targets.extend(
            self.ai_logic.target_finder.find_weapons(player_pos_xy, player_floor_id)
        )
        # 3. Armor pieces
        targets.extend(
            self.ai_logic.target_finder.find_armor(player_pos_xy, player_floor_id)
        )
        # 4. Quest Items
        targets.extend(
            self.ai_logic.target_finder.find_quest_items(player_pos_xy, player_floor_id)
        )
        # 5. Portals
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
        # 6. Other items
        targets.extend(
            self.ai_logic.target_finder.find_other_items(player_pos_xy, player_floor_id)
        )
        # 7. Monsters (lowest priority)
        targets.extend(
            self.ai_logic.target_finder.find_monsters(player_pos_xy, player_floor_id)
        )
        return targets

    def _target_sort_key(self, target_data):
        _, _, _, target_type, dist = target_data
        priority_map = {
            "health_potion": 1,
            "weapon": 2,
            "armor": 3,
            "quest_item": 4,
            "unvisited_portal": 5,
            "portal_to_unexplored": 6,
            "other_item": 7,
            "monster": 8,
        }
        priority = priority_map.get(target_type, 9)
        return (priority, dist)

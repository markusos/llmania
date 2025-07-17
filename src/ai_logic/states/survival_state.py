from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_state import AIState

if TYPE_CHECKING:
    pass


class SurvivalState(AIState):
    def handle_transitions(self) -> str:
        player = self.ai_logic.player
        if player.health > player.max_health / 2:
            return "ExploringState"
        return "SurvivalState"

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        # 1. Use Health Potion if available
        action = self._use_item("heal")
        if action:
            return action

        # 2. Flee from adjacent monsters
        if self.ai_logic._get_adjacent_monsters():
            if self.ai_logic._is_in_loop():
                self.ai_logic._break_loop()
                return None

            safe_moves = self._get_safe_moves()
            if safe_moves:
                move_command = self.ai_logic.random.choice(safe_moves)
                self.ai_logic.message_log.add_message(
                    "AI: Low health, fleeing from monster."
                )
                return move_command

        # 3. Take item on current tile (e.g., a health potion)
        action = self._pickup_item()
        if action:
            return action

        # 4. Path to the most important target
        path_action = self._path_to_best_target(
            self._find_best_target, self._target_sort_key
        )
        if path_action:
            return path_action

        # 5. If no other options, explore to find potions
        exploration_path = self.ai_logic.explorer.find_exploration_targets(
            (self.ai_logic.player.x, self.ai_logic.player.y),
            self.ai_logic.player.current_floor_id,
        )
        if exploration_path:
            self.ai_logic.current_path = exploration_path
            return self._follow_path()

        return self._explore_randomly()

    def _get_safe_moves(self) -> list[Tuple[str, str]]:
        safe_moves = []
        possible_moves = {
            "north": (0, -1),
            "south": (0, 1),
            "west": (-1, 0),
            "east": (1, 0),
        }
        for move, (dx, dy) in possible_moves.items():
            check_x, check_y = self.ai_logic.player.x + dx, self.ai_logic.player.y + dy
            current_ai_map = self.ai_logic.ai_visible_maps.get(
                self.ai_logic.player.current_floor_id
            )
            if not current_ai_map:
                continue
            tile = current_ai_map.get_tile(check_x, check_y)
            if tile and tile.type != "wall" and not tile.monster:
                safe_moves.append(("move", move))
        return safe_moves

    def _find_best_target(self, player_pos_xy, player_floor_id):
        targets = []
        # 1. Survival: Find health potions if low on health
        targets.extend(
            self.ai_logic.target_finder.find_health_potions(
                player_pos_xy, player_floor_id, same_floor_only=True
            )
        )
        # 2. Quest Items
        targets.extend(
            self.ai_logic.target_finder.find_quest_items(
                player_pos_xy, player_floor_id, same_floor_only=True
            )
        )
        # 3. Other items
        targets.extend(
            self.ai_logic.target_finder.find_other_items(
                player_pos_xy, player_floor_id, same_floor_only=True
            )
        )
        return targets

    def _target_sort_key(self, target_data):
        _, _, _, target_type, dist = target_data
        priority = 5
        if target_type == "health_potion":
            priority = 1
        elif target_type == "quest_item":
            priority = 2
        elif target_type == "unvisited_portal":
            priority = 3
        elif target_type == "portal_to_unexplored":
            priority = 4
        return (priority, dist)

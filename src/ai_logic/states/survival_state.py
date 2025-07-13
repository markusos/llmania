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
        for item in self.ai_logic.player.inventory:
            if item.properties.get("type") == "heal":
                self.ai_logic.message_log.add_message(
                    f"AI: Low health, using {item.name}."
                )
                return ("use", item.name)

        # 2. Flee from adjacent monsters
        adjacent_monsters = self.ai_logic._get_adjacent_monsters()
        if adjacent_monsters:
            # Calculate a "safe" direction away from monsters
            safe_moves = self._get_safe_moves()
            if safe_moves:
                move_direction = self.ai_logic.random.choice(safe_moves)
                self.ai_logic.message_log.add_message(
                    "AI: Low health, fleeing from monster."
                )
                return ("move", move_direction)

        # 3. Find health potions on the map
        player_pos_xy = (self.ai_logic.player.x, self.ai_logic.player.y)
        player_floor_id = self.ai_logic.player.current_floor_id
        health_potions = self.ai_logic.target_finder.find_health_potions(
            player_pos_xy, player_floor_id
        )
        health_potions = [
            potion
            for potion in health_potions
            if (potion[0], potion[1]) != player_pos_xy or potion[2] != player_floor_id
        ]
        if health_potions:
            target_x, target_y, target_floor_id, _, _ = health_potions[0]
            path = self.ai_logic.path_finder.find_path_bfs(
                self.ai_logic.ai_visible_maps,
                player_pos_xy,
                player_floor_id,
                (target_x, target_y),
                target_floor_id,
            )
            if path:
                log_msg = (
                    "AI: Low health, pathing to health potion at "
                    f"({target_x},{target_y}) on floor {target_floor_id}."
                )
                self.ai_logic.message_log.add_message(log_msg)
                self.ai_logic.current_path = path
                return self._follow_path()

        # 4. If no other options, explore to find potions
        exploration_path = self.ai_logic.explorer.find_exploration_targets(
            player_pos_xy, player_floor_id
        )
        if exploration_path:
            self.ai_logic.current_path = exploration_path
            return self._follow_path()

        return self._explore_randomly()

    def _get_safe_moves(self) -> list[str]:
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
                safe_moves.append(move)
        return safe_moves

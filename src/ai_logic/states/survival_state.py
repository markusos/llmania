from __future__ import annotations

from typing import Optional, Tuple

from .base_state import AIState


class SurvivalState(AIState):
    def handle_transitions(self) -> str:
        # Exit survival if we're healthy again (use dynamic threshold)
        if not self.ai_logic.should_enter_survival_mode():
            # Check if there are safe monsters to attack
            if self.ai_logic._get_adjacent_monsters():
                safe_monster = self.ai_logic.get_safest_adjacent_monster()
                if safe_monster:
                    return "AttackingState"
            return "ExploringState"
        return "SurvivalState"

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        # 1. Use Health Potion if available
        action = self._use_item("heal")
        if action:
            return action

        # 2. Flee from adjacent monsters
        adjacent_monsters = self.ai_logic._get_adjacent_monsters()
        if adjacent_monsters:
            if self.ai_logic._is_in_loop():
                self.ai_logic._break_loop()
                return None

            # Try intelligent flee direction first
            # (maximizes distance from threats, avoids dead ends)
            best_flee = self._get_best_flee_direction()
            if best_flee:
                self.ai_logic.message_log.add_message(
                    "AI: Low health, fleeing from monster (optimal direction)."
                )
                return best_flee

            # Fall back to any safe move if no optimal direction found
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
            (self.ai_logic.player_view.x, self.ai_logic.player_view.y),
            self.ai_logic.player_view.current_floor_id,
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
            player_view = self.ai_logic.player_view
            check_x, check_y = player_view.x + dx, player_view.y + dy
            current_ai_map = self.ai_logic.ai_visible_maps.get(
                player_view.current_floor_id
            )
            if not current_ai_map:
                continue
            tile = current_ai_map.get_tile(check_x, check_y)
            if tile and tile.type != "wall" and not tile.monster:
                safe_moves.append(("move", move))
        return safe_moves

    def _is_safe_move(self, x: int, y: int) -> bool:
        """Check if a position is safe to move to (not wall, not monster)."""
        current_ai_map = self.ai_logic.ai_visible_maps.get(
            self.ai_logic.player_view.current_floor_id
        )
        if not current_ai_map:
            return False
        tile = current_ai_map.get_tile(x, y)
        return tile is not None and tile.type != "wall" and not tile.monster

    def _count_exits(self, x: int, y: int) -> int:
        """Count number of safe exits from a position (excludes monsters and walls)."""
        exits = 0
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            if self._is_safe_move(x + dx, y + dy):
                exits += 1
        return exits

    def _get_best_flee_direction(self) -> Optional[Tuple[str, str]]:
        """Find direction that maximizes distance from threats and avoids dead ends."""
        adjacent_monsters = self.ai_logic._get_adjacent_monsters()
        if not adjacent_monsters:
            return None

        # Calculate threat center (centroid of all adjacent monsters)
        threat_x = sum(m.x for m in adjacent_monsters) / len(adjacent_monsters)
        threat_y = sum(m.y for m in adjacent_monsters) / len(adjacent_monsters)

        player_view = self.ai_logic.player_view
        best_direction = None
        best_score = float("-inf")

        for direction, (dx, dy) in [
            ("north", (0, -1)),
            ("south", (0, 1)),
            ("west", (-1, 0)),
            ("east", (1, 0)),
        ]:
            new_x = player_view.x + dx
            new_y = player_view.y + dy

            if self._is_safe_move(new_x, new_y):
                # Calculate distance from threat center (higher is better)
                dist = abs(new_x - threat_x) + abs(new_y - threat_y)

                # Count exits from the new position (more exits = less likely dead end)
                exits = self._count_exits(new_x, new_y)

                # Penalize dead ends heavily (0-1 exits), prefer open areas (3-4 exits)
                # Score = distance + exit_bonus
                # Dead end (0-1 exits): penalty of -10
                # Corner (2 exits): neutral
                # Open area (3-4 exits): bonus of +2 to +4
                if exits <= 1:
                    exit_bonus = -10  # Avoid dead ends at all costs
                elif exits == 2:
                    exit_bonus = 0  # Corridor or corner, acceptable
                else:
                    exit_bonus = exits  # Open areas are good

                score = dist + exit_bonus

                if score > best_score:
                    best_score = score
                    best_direction = ("move", direction)

        return best_direction

    def _find_best_target(self, player_pos_xy, player_floor_id):
        targets = []
        # 1. Survival: Find health potions if low on health (check all floors)
        targets.extend(
            self.ai_logic.target_finder.find_health_potions(
                player_pos_xy, player_floor_id, same_floor_only=False
            )
        )
        # 2. Quest Items (check all floors)
        targets.extend(
            self.ai_logic.target_finder.find_quest_items(
                player_pos_xy, player_floor_id, same_floor_only=False
            )
        )
        # 3. Portals to unexplored floors (important for not getting stuck)
        targets.extend(
            self.ai_logic.explorer.find_portal_to_unexplored_floor(
                player_pos_xy, player_floor_id
            )
        )
        # 4. Unvisited portals
        targets.extend(
            self.ai_logic.explorer.find_unvisited_portals(
                player_pos_xy, player_floor_id
            )
        )
        # 5. Other items (check all floors)
        targets.extend(
            self.ai_logic.target_finder.find_other_items(
                player_pos_xy, player_floor_id, same_floor_only=False
            )
        )
        return targets

    def _target_sort_key(self, target_data):
        _, _, _, target_type, dist = target_data
        priority_map = {
            "health_potion": 1,
            "quest_item": 2,
            "portal_to_unexplored": 3,
            "unvisited_portal": 4,
            "other_item": 5,
        }
        priority = priority_map.get(target_type, 6)
        return (priority, dist)

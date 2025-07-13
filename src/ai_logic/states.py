from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from src.ai_logic.main import AILogic


class AIState:
    def __init__(self, ai_logic: "AILogic"):
        self.ai_logic = ai_logic

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        raise NotImplementedError


class ExploringState(AIState):
    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        self.ai_logic.current_path = None
        player_pos_xy = (self.ai_logic.player.x, self.ai_logic.player.y)
        player_floor_id = self.ai_logic.player.current_floor_id

        # 1. Survival: Find health potions if low on health
        health_potions = self.ai_logic.target_finder.find_health_potions(
            player_pos_xy, player_floor_id
        )
        if health_potions:
            targets = health_potions
        else:
            # 2. Quest Items
            quest_items = self.ai_logic.target_finder.find_quest_items(
                player_pos_xy, player_floor_id
            )
            if quest_items:
                targets = quest_items
            else:
                # 3. Exploration
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
                    return self.ai_logic._follow_path()

                # 4. Other targets if exploration is complete
                targets = []
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
                    self.ai_logic.target_finder.find_other_items(
                        player_pos_xy, player_floor_id
                    )
                )
                targets.extend(
                    self.ai_logic.target_finder.find_monsters(
                        player_pos_xy, player_floor_id
                    )
                )

        def target_sort_key(target_data):
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

        targets.sort(key=target_sort_key)

        for target_x, target_y, target_floor_id, target_type, _ in targets:
            path = self.ai_logic.path_finder.find_path_bfs(
                self.ai_logic.ai_visible_maps,
                player_pos_xy,
                player_floor_id,
                (target_x, target_y),
                target_floor_id,
            )
            if path:
                log_msg = (
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) on "
                    f"floor {target_floor_id}."
                )
                self.ai_logic.message_log.add_message(log_msg)
                self.ai_logic.current_path = path
                break

        if not self.ai_logic.current_path:
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

        if self.ai_logic.current_path:
            return self.ai_logic._follow_path()
        else:
            self.ai_logic.message_log.add_message(
                "AI: No path found for any target or exploration."
            )
            return self.ai_logic._explore_randomly()


class AttackingState(AIState):
    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        player = self.ai_logic.player
        if player.health <= player.max_health / 2:
            self.ai_logic.state = SurvivalState(self.ai_logic)
            return self.ai_logic.state.get_next_action()

        adjacent_monsters = self.ai_logic._get_adjacent_monsters()
        if adjacent_monsters:
            monster_to_attack = self.ai_logic.random.choice(adjacent_monsters)
            self.ai_logic.message_log.add_message(
                f"AI: Attacking adjacent {monster_to_attack.name}."
            )
            self.ai_logic.current_path = None
            return ("attack", monster_to_attack.name)
        else:
            # If no adjacent monsters, switch back to exploring
            self.ai_logic.state = ExploringState(self.ai_logic)
            return self.ai_logic.state.get_next_action()


class LootingState(AIState):
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
                log_msg = (
                    f"AI: Pathing to item at ({target_x},{target_y}) on floor "
                    f"{target_floor_id}."
                )
                self.ai_logic.message_log.add_message(log_msg)
                self.ai_logic.current_path = path
                return self.ai_logic._follow_path()

        # 5. If no items to loot, switch back to exploring
        self.ai_logic.state = ExploringState(self.ai_logic)
        return self.ai_logic.state.get_next_action()


class SurvivalState(AIState):
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
            safe_moves = self.ai_logic._get_safe_moves()
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
                return self.ai_logic._follow_path()

        # 4. If no other options, explore to find potions
        exploration_path = self.ai_logic.explorer.find_exploration_targets(
            player_pos_xy, player_floor_id
        )
        if exploration_path:
            self.ai_logic.current_path = exploration_path
            return self.ai_logic._follow_path()

        return self.ai_logic._explore_randomly()

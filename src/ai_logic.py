import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder

if TYPE_CHECKING:
    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap


class AILogic:
    """
    Handles the decision-making for AI-controlled characters, primarily the player
    when AI mode is active.
    """

    def __init__(
        self,
        player: "Player",
        real_world_maps: Dict[int, "WorldMap"],
        ai_visible_maps: Dict[int, "WorldMap"],
        message_log: "MessageLog",
    ):
        self.player = player
        self.real_world_maps = real_world_maps
        self.ai_visible_maps = ai_visible_maps
        self.message_log = message_log
        self.path_finder = PathFinder()
        self.physically_visited_coords: List[Tuple[int, int, int]] = []
        self.current_path: Optional[List[Tuple[int, int, int]]] = None
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None

    def update_visibility(self) -> None:
        player_x, player_y = self.player.x, self.player.y
        current_floor_id = self.player.current_floor_id
        current_real_map = self.real_world_maps.get(current_floor_id)
        current_ai_visible_map = self.ai_visible_maps.get(current_floor_id)

        if not current_real_map or not current_ai_visible_map:
            msg = (
                f"AI Error: Cannot update visibility for floor {current_floor_id}. "
                "Map not found."
            )
            self.message_log.add_message(msg)
            return
        for dy_offset in range(-1, 2):
            for dx_offset in range(-1, 2):
                map_x, map_y = player_x + dx_offset, player_y + dy_offset
                real_tile = current_real_map.get_tile(map_x, map_y)
                if real_tile:
                    ai_tile = current_ai_visible_map.get_tile(map_x, map_y)
                    if ai_tile:
                        ai_tile.type = real_tile.type
                        ai_tile.monster = real_tile.monster
                        ai_tile.item = real_tile.item
                        ai_tile.is_portal = real_tile.is_portal
                        ai_tile.portal_to_floor_id = real_tile.portal_to_floor_id
                        ai_tile.is_explored = True

    def _get_adjacent_monsters(self) -> List["Monster"]:
        adjacent_monsters: List["Monster"] = []
        current_floor_id = self.player.current_floor_id
        current_ai_map = self.ai_visible_maps.get(current_floor_id)
        if not current_ai_map:
            return []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_x, check_y = self.player.x + dx, self.player.y + dy
            tile = current_ai_map.get_tile(check_x, check_y)
            if tile and tile.is_explored and tile.monster:
                adjacent_monsters.append(tile.monster)
        return adjacent_monsters

    def _coordinates_to_move_command(
        self, start_pos_xy: Tuple[int, int], end_pos_xy: Tuple[int, int]
    ) -> Optional[Tuple[str, str]]:
        dx = end_pos_xy[0] - start_pos_xy[0]
        dy = end_pos_xy[1] - start_pos_xy[1]
        if dx == 0 and dy == -1:
            return ("move", "north")
        if dx == 0 and dy == 1:
            return ("move", "south")
        if dx == -1 and dy == 0:
            return ("move", "west")
        if dx == 1 and dy == 0:
            return ("move", "east")
        return None

    def _find_target_and_path(self) -> None:
        self.current_path = None
        player_pos_xy = (self.player.x, self.player.y)
        player_floor_id = self.player.current_floor_id
        current_ai_map = self.ai_visible_maps.get(player_floor_id)
        if not current_ai_map:
            self.message_log.add_message(
                "AI: Current floor map not available for targeting."
            )
            return

        found_targets: List[Tuple[int, int, int, str, int]] = []

        # 1. Quest Items
        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            for y_coord in range(ai_map.height):
                for x_coord in range(ai_map.width):
                    tile = ai_map.get_tile(x_coord, y_coord)
                    if (tile and tile.is_explored and tile.item and
                            tile.item.properties.get("type") == "quest"):
                        dist_est = (
                            abs(x_coord - player_pos_xy[0]) +
                            abs(y_coord - player_pos_xy[1]) +
                            abs(floor_id - player_floor_id) * 10
                        )
                        found_targets.append(
                            (x_coord, y_coord, floor_id, "quest_item", dist_est)
                        )

        # 2. Health Potions (if low health) or Other Items
        low_health_threshold = self.player.max_health * 0.5
        if self.player.health < low_health_threshold:
            for floor_id, ai_map in self.ai_visible_maps.items():
                if not ai_map:
                    continue
                for y_coord in range(ai_map.height):
                    for x_coord in range(ai_map.width):
                        tile = ai_map.get_tile(x_coord, y_coord)
                        if (tile and tile.is_explored and tile.item and
                                "health potion" in tile.item.name.lower() and
                                tile.item.properties.get("type") == "heal"):
                            dist_est = (
                                abs(x_coord - player_pos_xy[0]) +
                                abs(y_coord - player_pos_xy[1]) +
                                abs(floor_id - player_floor_id) * 10
                            )
                            found_targets.append(
                                (x_coord, y_coord, floor_id, "health_potion", dist_est)
                            )
        else:  # Not low health, look for other items
            for floor_id, ai_map in self.ai_visible_maps.items():
                if not ai_map:
                    continue
                for y_coord_item in range(ai_map.height):
                    for x_coord_item in range(ai_map.width):
                        tile = ai_map.get_tile(x_coord_item, y_coord_item)
                        player_at_target = (
                            x_coord_item == player_pos_xy[0] and
                            y_coord_item == player_pos_xy[1] and
                            floor_id == player_floor_id
                        )
                        if tile and tile.is_explored and tile.item and \
                           not player_at_target:
                            is_potion_full_health = (
                                tile.item.properties.get("type") == "heal" and
                                "health potion" in tile.item.name.lower() and
                                self.player.health >= self.player.max_health
                            )
                            is_quest_item = tile.item.properties.get("type") == "quest"
                            if is_potion_full_health or is_quest_item:
                                continue
                            dist_est = (
                                abs(x_coord_item - player_pos_xy[0]) +
                                abs(y_coord_item - player_pos_xy[1]) +
                                abs(floor_id - player_floor_id) * 10
                            )
                            found_targets.append(
                                (x_coord_item, y_coord_item, floor_id,
                                 "other_item", dist_est)
                            )

        # 3. Monsters
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
                                if (player_pos_xy[0] + dx_adj == x_monster and
                                        player_pos_xy[1] + dy_adj == y_monster):
                                    is_adjacent = True
                                    break
                        if not is_adjacent:
                            dist_est = (
                                abs(x_monster - player_pos_xy[0]) +
                                abs(y_monster - player_pos_xy[1]) +
                                abs(floor_id - player_floor_id) * 10
                            )
                            found_targets.append(
                                (x_monster, y_monster, floor_id, "monster", dist_est)
                            )

        def target_sort_key(target_data):
            _, _, _, target_type, dist = target_data
            priority = 5
            if target_type == "quest_item":
                priority = 1
            elif target_type == "health_potion":
                priority = 2
            elif target_type == "monster":
                priority = 3
            return (priority, dist)
        found_targets.sort(key=target_sort_key)

        for target_x, target_y, target_floor_id, target_type, _ in found_targets:
            path = self.path_finder.find_path_bfs(
                self.ai_visible_maps, player_pos_xy, player_floor_id,
                (target_x, target_y), target_floor_id
            )
            if path:
                log_msg = (
                    f"AI: Pathing to {target_type} at ({target_x},{target_y}) on "
                    f"floor {target_floor_id}."
                )
                self.message_log.add_message(log_msg)
                self.current_path = path
                return

        explorable_physically_unvisited_coords_current_floor: List[Tuple[int, int]] = []
        if current_ai_map:
            for y_explore in range(current_ai_map.height):
                for x_explore in range(current_ai_map.width):
                    tile = current_ai_map.get_tile(x_explore, y_explore)
                    condition = (
                        tile and tile.is_explored and tile.type != "wall" and
                        (x_explore, y_explore, player_floor_id)
                        not in self.physically_visited_coords
                    )
                    if condition:
                        explorable_physically_unvisited_coords_current_floor.append(
                            (x_explore, y_explore)
                        )
        if explorable_physically_unvisited_coords_current_floor:
            paths_to_explore_unvisited = []
            for coord_xy in explorable_physically_unvisited_coords_current_floor:
                path = self.path_finder.find_path_bfs(
                    self.ai_visible_maps, player_pos_xy, player_floor_id,
                    coord_xy, player_floor_id
                )
                if path:
                    paths_to_explore_unvisited.append(path)
            if paths_to_explore_unvisited:
                paths_to_explore_unvisited.sort(key=len)
                self.current_path = paths_to_explore_unvisited[0]
                target_coord = self.current_path[-1]
                log_msg = (
                    f"AI: Pathing to explore unvisited tile at ({target_coord[0]},"
                    f"{target_coord[1]}) on current floor."
                )
                self.message_log.add_message(log_msg)
                return

        edge_exploration_targets_current_floor: List[Tuple[int, int]] = []
        if current_ai_map:
            for y_edge in range(current_ai_map.height):
                for x_edge in range(current_ai_map.width):
                    tile = current_ai_map.get_tile(x_edge,y_edge)
                    if tile and tile.is_explored and tile.type != "wall":
                        for dx_adj, dy_adj in [(0,-1),(0,1),(-1,0),(1,0)]:
                            adj_x, adj_y = x_edge + dx_adj, y_edge + dy_adj
                            adj_tile = current_ai_map.get_tile(adj_x, adj_y)
                            if adj_tile and not adj_tile.is_explored:
                                if (x_edge, y_edge) not in \
                                   edge_exploration_targets_current_floor:
                                    edge_exploration_targets_current_floor.append(
                                        (x_edge, y_edge)
                                    )
                                break
        if edge_exploration_targets_current_floor:
            paths_to_edge_frontiers = []
            for coord_xy in edge_exploration_targets_current_floor:
                if coord_xy == player_pos_xy:
                    continue
                path = self.path_finder.find_path_bfs(
                    self.ai_visible_maps, player_pos_xy, player_floor_id,
                    coord_xy, player_floor_id
                )
                if path:
                    paths_to_edge_frontiers.append(path)
            if paths_to_edge_frontiers:
                paths_to_edge_frontiers.sort(key=len)
                self.current_path = paths_to_edge_frontiers[0]
                target_coord = self.current_path[-1]
                log_msg = (
                    f"AI: Pathing to edge of known area at ({target_coord[0]},"
                    f"{target_coord[1]}) on current floor."
                )
                self.message_log.add_message(log_msg)
                return
        self.message_log.add_message(
            "AI: No path found for any target or exploration."
        )

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        self.update_visibility()
        player_pos_xyz = (self.player.x, self.player.y, self.player.current_floor_id)
        if player_pos_xyz not in self.physically_visited_coords:
            self.physically_visited_coords.append(player_pos_xyz)
        current_ai_map = self.ai_visible_maps.get(player_pos_xyz[2])
        if not current_ai_map:
            self.message_log.add_message(
                "AI: Critical error - current AI map not found."
            )
            return ("look", None)
        current_tile_on_visible_map = current_ai_map.get_tile(
            player_pos_xyz[0], player_pos_xyz[1]
        )

        if (current_tile_on_visible_map and
            current_tile_on_visible_map.is_explored and
            current_tile_on_visible_map.item and
            current_tile_on_visible_map.item.properties.get("type") == "quest"):
            item_name = current_tile_on_visible_map.item.name
            self.message_log.add_message(f"AI: Found quest item {item_name}!")
            self.current_path = None
            return ("take", item_name)

        low_health_threshold = self.player.max_health * 0.5
        if self.player.health < low_health_threshold:
            health_potion_inv = next(
                (item for item in self.player.inventory
                 if "health potion" in item.name.lower() and
                    item.properties.get("type") == "heal"),
                None,
            )
            if health_potion_inv:
                self.message_log.add_message(
                    "AI: Low health, using Health Potion from inventory."
                )
                self.current_path = None
                return ("use", health_potion_inv.name)

        if (current_tile_on_visible_map and
            current_tile_on_visible_map.is_explored and
            current_tile_on_visible_map.item):
            item_is_potion = (
                "health potion" in current_tile_on_visible_map.item.name.lower() and
                current_tile_on_visible_map.item.properties.get("type") == "heal"
            )
            if item_is_potion and self.player.health >= self.player.max_health:
                log_msg = (
                    f"AI: On tile with {current_tile_on_visible_map.item.name}, "
                    "but health is full. Skipping."
                )
                self.message_log.add_message(log_msg)
            else:
                item_name = current_tile_on_visible_map.item.name
                self.message_log.add_message(
                    f"AI: Found item {item_name} on current tile, taking it."
                )
                self.current_path = None
                return ("take", item_name)

        adjacent_monsters = self._get_adjacent_monsters()
        if adjacent_monsters:
            monster_to_attack = random.choice(adjacent_monsters)
            self.message_log.add_message(
                f"AI: Attacking adjacent {monster_to_attack.name}."
            )
            self.current_path = None
            return ("attack", monster_to_attack.name)

        if self.current_path:
            current_pos_xyz = (
                self.player.x, self.player.y, self.player.current_floor_id
            )
            if self.current_path[0] == current_pos_xyz:
                self.current_path.pop(0)
            if not self.current_path:
                self.current_path = None
            else:
                next_step_xyz = self.current_path[0]
                next_step_map = self.ai_visible_maps.get(next_step_xyz[2])
                if not next_step_map:
                    self.message_log.add_message(
                        "AI: Path leads to an unknown floor, recalculating."
                    )
                    self.current_path = None
                else:
                    next_tile_visible = next_step_map.get_tile(
                        next_step_xyz[0], next_step_xyz[1]
                    )
                    can_move_to_next_step = False
                    if next_tile_visible and next_tile_visible.is_explored:
                        if next_tile_visible.type != "wall":
                            if next_tile_visible.monster:
                                if next_step_xyz == self.current_path[-1]:
                                    can_move_to_next_step = True
                            else:
                                can_move_to_next_step = True
                        elif next_tile_visible.is_portal and \
                             next_step_xyz[2] != current_pos_xyz[2]:
                             can_move_to_next_step = True
                    if not can_move_to_next_step:
                        self.message_log.add_message(
                            "AI: Path blocked or invalid on visible map, "
                            "recalculating."
                        )
                        self.current_path = None
                    else:
                        move_command = self._coordinates_to_move_command(
                            (current_pos_xyz[0], current_pos_xyz[1]),
                            (next_step_xyz[0], next_step_xyz[1])
                        )
                        if move_command:
                            log_msg = (
                                f"AI: Following path. Moving {move_command[1]} to "
                                f"({next_step_xyz[0]},{next_step_xyz[1]}) on floor "
                                f"{next_step_xyz[2]}."
                            )
                            self.message_log.add_message(log_msg)
                            self.last_move_command = move_command
                            return move_command
                        else:
                            self.message_log.add_message(
                                "AI: Error in path following (non-adjacent step), "
                                "recalculating."
                            )
                            self.current_path = None
        if not self.current_path:
            self._find_target_and_path()
            if self.current_path:
                current_pos_xyz = (
                    self.player.x, self.player.y, self.player.current_floor_id
                )
                if self.current_path[0] == current_pos_xyz:
                    self.current_path.pop(0)
                if not self.current_path:
                    self.message_log.add_message(
                        "AI: New path target is current location. Looking around."
                    )
                    self.last_move_command = ("look", None)
                    return ("look", None)
                next_step_xyz = self.current_path[0]
                next_step_map = self.ai_visible_maps.get(next_step_xyz[2])
                can_move_to_first_step = False
                if next_step_map:
                    first_step_tile = next_step_map.get_tile(
                        next_step_xyz[0], next_step_xyz[1]
                    )
                    if first_step_tile and first_step_tile.is_explored:
                        if first_step_tile.type != "wall":
                            if first_step_tile.monster:
                                if next_step_xyz == self.current_path[-1]:
                                    can_move_to_first_step = True
                            else:
                                can_move_to_first_step = True
                        elif first_step_tile.is_portal and \
                             next_step_xyz[2] != current_pos_xyz[2]:
                            can_move_to_first_step = True
                if not can_move_to_first_step:
                    self.message_log.add_message(
                        "AI: First step of new path blocked. Looking around."
                    )
                    self.current_path = None
                    self.last_move_command = ("look", None)
                    return ("look", None)
                move_command = self._coordinates_to_move_command(
                     (current_pos_xyz[0], current_pos_xyz[1]),
                     (next_step_xyz[0], next_step_xyz[1])
                )
                if move_command:
                    log_msg = (
                        f"AI: Starting new path. Moving {move_command[1]} to "
                        f"({next_step_xyz[0]},{next_step_xyz[1]}) on floor "
                        f"{next_step_xyz[2]}."
                    )
                    self.message_log.add_message(log_msg)
                    self.last_move_command = move_command
                    return move_command
                else:
                    self.message_log.add_message(
                        "AI: Error in new path step. Looking around."
                    )
                    self.current_path = None
                    self.last_move_command = ("look", None)
                    return ("look", None)

        possible_moves_current_floor = []
        if current_ai_map:
            player_pos_xy = (player_pos_xyz[0], player_pos_xyz[1])
            for direction, (dx, dy) in [("north",(0,-1)), ("south",(0,1)),
                                        ("west",(-1,0)), ("east",(1,0))]:
                check_x, check_y = player_pos_xy[0] + dx, player_pos_xy[1] + dy
                if current_ai_map.is_valid_move(check_x, check_y):
                    possible_moves_current_floor.append(("move", direction))
        if possible_moves_current_floor:
            unvisited_moves = []
            for move_cmd, direction_str in possible_moves_current_floor:
                dx_m, dy_m = {"north":(0,-1),"south":(0,1),
                              "west":(-1,0),"east":(1,0)}[direction_str]
                check_x_m = player_pos_xyz[0] + dx_m
                check_y_m = player_pos_xyz[1] + dy_m
                if ((check_x_m, check_y_m, player_pos_xyz[2])
                        not in self.physically_visited_coords):
                    unvisited_moves.append((move_cmd, direction_str))
            if unvisited_moves:
                chosen_move = unvisited_moves[0]
                self.message_log.add_message( # E501: Wrapped f-string
                    f"AI: Exploring unvisited on current floor. "
                    f"Moving {chosen_move[1]}."
                )
                self.last_move_command = chosen_move
                return chosen_move
            else:
                chosen_move = random.choice(possible_moves_current_floor)
                self.message_log.add_message(
                    f"AI: All nearby visited on current floor. Moving {chosen_move[1]}."
                )
                self.last_move_command = chosen_move
                return chosen_move
        self.message_log.add_message("AI: No actions available. Looking around.")
        self.last_move_command = ("look", None)
        return ("look", None)

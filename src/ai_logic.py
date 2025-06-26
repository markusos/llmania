import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder

if TYPE_CHECKING:
    from src.monster import Monster # Corrected import
    from src.message_log import MessageLog
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
        real_world_map: "WorldMap", # The actual full map
        ai_visible_map: "WorldMap", # The map AI uses for decisions
        message_log: "MessageLog",
    ):
        """
        Initializes the AILogic system.

        Args:
            player: The player object that the AI will control.
            real_world_map: The complete game world map.
            ai_visible_map: The map representing what the AI can currently see.
            message_log: The message log for recording actions or observations.
        """
        self.player = player
        self.real_world_map = real_world_map # Store the real map for updating visibility
        self.ai_visible_map = ai_visible_map # This is the map AI will use for decisions
        self.message_log = message_log
        self.path_finder = PathFinder()
        # physically_visited_coords tracks tiles the AI has actually stepped on.
        self.physically_visited_coords: List[Tuple[int, int]] = []
        self.current_path: Optional[List[Tuple[int, int]]] = None
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None

    def update_visibility(self) -> None:
        """
        Updates the AI's visible map based on the player's current position
        on the real map. Reveals tiles in a 1-tile radius (8 directions + current tile).
        """
        player_x, player_y = self.player.x, self.player.y

        for dy in range(-1, 2):  # -1, 0, 1
            for dx in range(-1, 2):  # -1, 0, 1
                # No need to check dx == 0 and dy == 0 if we always update current tile
                # if dx == 0 and dy == 0:
                #     continue # Skip the player's current tile, handled separately or included

                map_x, map_y = player_x + dx, player_y + dy

                real_tile = self.real_world_map.get_tile(map_x, map_y)
                if real_tile:
                    # Get the corresponding tile in the AI's visible map
                    ai_tile = self.ai_visible_map.get_tile(map_x, map_y)
                    if ai_tile:
                        # Copy data from real tile to AI's visible tile
                        ai_tile.type = real_tile.type
                        ai_tile.monster = real_tile.monster # Monster objects are shared
                        ai_tile.item = real_tile.item # Item objects are shared
                        ai_tile.is_explored = True # Mark as explored in AI's map
                        # self.physically_visited_coords is updated in get_next_action


    def _get_adjacent_monsters(self) -> List["Monster"]:
        """
        Checks N, S, E, W tiles around the player for monsters using the AI's visible map.
        """
        adjacent_monsters: List["Monster"] = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # N, S, W, E
            check_x, check_y = self.player.x + dx, self.player.y + dy
            # Use ai_visible_map for decision making
            tile = self.ai_visible_map.get_tile(check_x, check_y)
            if tile and tile.is_explored and tile.monster:
                adjacent_monsters.append(tile.monster)
        return adjacent_monsters

    def _coordinates_to_move_command(
        self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]
    ) -> Optional[Tuple[str, str]]:
        """
        Converts a move from start_pos to an adjacent end_pos into a move command.
        """
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]

        if dx == 0 and dy == -1:
            return ("move", "north")
        if dx == 0 and dy == 1:
            return ("move", "south")
        if dx == -1 and dy == 0:
            return ("move", "west")
        if dx == 1 and dy == 0:
            return ("move", "east")
        return None # Should not happen for adjacent tiles

    def _find_target_and_path(self) -> None:
        """
        Finds a target (quest item, other item, monster, unvisited tile) and
        calculates a path to it. Sets self.current_path.
        """
        self.current_path = None
        player_pos = (self.player.x, self.player.y)

        # All checks for items, monsters, and pathing should use self.ai_visible_map
        # and respect tile.is_explored.

        target_type_sought = "any" # For logging

        # 1. Quest Item (must be visible)
        for y in range(self.ai_visible_map.height):
            for x in range(self.ai_visible_map.width):
                tile = self.ai_visible_map.get_tile(x, y)
                if (
                    tile
                    and tile.is_explored # Must be seen
                    and tile.item
                    and tile.item.properties.get("type") == "quest"
                ):
                    # Pathfind on the ai_visible_map
                    path = self.path_finder.find_path_bfs(
                        self.ai_visible_map, player_pos, (x, y)
                    )
                    if path:
                        self.message_log.add_message(f"AI: Pathing to (visible) quest item at ({x},{y}).")
                        self.current_path = path
                        return

        # 2. Other Items (must be visible)
        #    - Health Potion if low health (priority)
        #    - Other items (unless potion and full health)

        low_health_threshold = self.player.max_health * 0.5
        if self.player.health < low_health_threshold:
            health_potions_coords: List[Tuple[int,int]] = []
            for y_coord in range(self.ai_visible_map.height):
                for x_coord in range(self.ai_visible_map.width):
                    tile = self.ai_visible_map.get_tile(x_coord, y_coord)
                    if tile and tile.is_explored and tile.item and \
                       "health potion" in tile.item.name.lower() and \
                       tile.item.properties.get("type") == "heal":
                        health_potions_coords.append((x_coord, y_coord))

            if health_potions_coords:
                paths_to_potions = []
                for coord in health_potions_coords:
                    path = self.path_finder.find_path_bfs(self.ai_visible_map, player_pos, coord)
                    if path:
                        paths_to_potions.append(path)
                if paths_to_potions:
                    paths_to_potions.sort(key=len)
                    self.current_path = paths_to_potions[0]
                    target_coord = self.current_path[-1]
                    self.message_log.add_message(f"AI: Low health, pathing to Health Potion at ({target_coord[0]},{target_coord[1]}).")
                    return


        other_items_coords: List[Tuple[int,int]] = []
        for y in range(self.ai_visible_map.height):
            for x in range(self.ai_visible_map.width):
                tile = self.ai_visible_map.get_tile(x, y)
                if tile and tile.is_explored and tile.item and (x,y) != player_pos:
                    # Skip potions if health is full
                    if tile.item.properties.get("type") == "heal" and \
                       "health potion" in tile.item.name.lower() and \
                       self.player.health >= self.player.max_health:
                        continue
                    # Skip quest items as they are handled above with higher priority
                    if tile.item.properties.get("type") == "quest":
                        continue
                    other_items_coords.append((x,y))

        if other_items_coords:
            paths_to_items = []
            for coord in other_items_coords:
                path = self.path_finder.find_path_bfs(self.ai_visible_map, player_pos, coord)
                if path:
                    paths_to_items.append(path)

            if paths_to_items:
                paths_to_items.sort(key=len)
                self.current_path = paths_to_items[0]
                target_coord = self.current_path[-1]
                item_name = self.ai_visible_map.get_tile(target_coord[0], target_coord[1]).item.name
                self.message_log.add_message(f"AI: Pathing to (visible) item {item_name} at ({target_coord[0]},{target_coord[1]}).")
                target_type_sought = "item"
                return

        # 3. Monsters (must be visible, not adjacent)
        monster_coords: List[Tuple[int,int]] = []
        for y in range(self.ai_visible_map.height):
            for x in range(self.ai_visible_map.width):
                tile = self.ai_visible_map.get_tile(x, y)
                if tile and tile.is_explored and tile.monster:
                    is_adjacent = False
                    for dx_adj, dy_adj in [(0, -1), (0, 1), (-1, 0), (1, 0)]: # N, S, W, E
                        if player_pos[0] + dx_adj == x and player_pos[1] + dy_adj == y:
                            is_adjacent = True
                            break
                    if not is_adjacent:
                         monster_coords.append((x,y))

        if monster_coords:
            paths_to_monsters = []
            for coord in monster_coords:
                path = self.path_finder.find_path_bfs(self.ai_visible_map, player_pos, coord)
                if path:
                    paths_to_monsters.append(path)

            if paths_to_monsters:
                paths_to_monsters.sort(key=len)
                self.current_path = paths_to_monsters[0]
                target_coord = self.current_path[-1]
                monster_name = self.ai_visible_map.get_tile(target_coord[0], target_coord[1]).monster.name
                self.message_log.add_message(f"AI: Pathing to (visible) monster {monster_name} at ({target_coord[0]},{target_coord[1]}).")
                target_type_sought = "monster"
                return

        # 4. Explore Unvisited but Revealed Floor Tiles (tiles that are known floor but not yet stepped on)
        #    or Explore towards edges of current visibility (tiles adjacent to known, but are themselves not explored)

        # First, explore known, walkable, but not physically stepped-on tiles.
        explorable_physically_unvisited_coords: List[Tuple[int,int]] = []
        for y in range(self.ai_visible_map.height):
            for x in range(self.ai_visible_map.width):
                tile = self.ai_visible_map.get_tile(x,y)
                if tile and tile.is_explored and tile.type != "wall" and \
                   (x,y) not in self.physically_visited_coords:
                    explorable_physically_unvisited_coords.append((x,y))

        if explorable_physically_unvisited_coords:
            paths_to_explore_unvisited = []
            for coord in explorable_physically_unvisited_coords:
                path = self.path_finder.find_path_bfs(self.ai_visible_map, player_pos, coord)
                if path:
                    paths_to_explore_unvisited.append(path)

            if paths_to_explore_unvisited:
                paths_to_explore_unvisited.sort(key=len)
                self.current_path = paths_to_explore_unvisited[0]
                target_coord = self.current_path[-1]
                self.message_log.add_message(f"AI: Pathing to explore known but unvisited tile at ({target_coord[0]},{target_coord[1]}).")
                target_type_sought = "unvisited known tile"
                return

        # Secondary: if all known walkable tiles have been physically visited, try to explore edges of fog.
        # Find a tile that is_explored and walkable, which is adjacent to a tile that is !is_explored.
        # Path to the known walkable tile.
        edge_exploration_targets: List[Tuple[int,int]] = [] # Store the known walkable tile to path to
        for y in range(self.ai_visible_map.height):
            for x in range(self.ai_visible_map.width):
                tile = self.ai_visible_map.get_tile(x,y)
                if tile and tile.is_explored and tile.type != "wall": # This is a known walkable tile
                    # Check its neighbors for an unexplored tile
                    for dx_adj, dy_adj in [(0,-1), (0,1), (-1,0), (1,0)]: # Orthogonal N,S,W,E
                        adj_x, adj_y = x + dx_adj, y + dy_adj
                        adj_tile = self.ai_visible_map.get_tile(adj_x, adj_y)
                        if adj_tile and not adj_tile.is_explored:
                            # (x,y) is a good candidate to path to, to reveal its neighbor (adj_x, adj_y)
                            if (x,y) not in edge_exploration_targets : # Avoid duplicates
                                edge_exploration_targets.append((x,y))
                            break # Found an unexplored neighbor for this tile, move to next tile

        if edge_exploration_targets:
            paths_to_edge_frontiers = []
            for coord in edge_exploration_targets:
                # Don't path to current player position if it's an edge frontier
                if coord == player_pos:
                    continue
                path = self.path_finder.find_path_bfs(self.ai_visible_map, player_pos, coord)
                if path:
                    paths_to_edge_frontiers.append(path)

            if paths_to_edge_frontiers:
                paths_to_edge_frontiers.sort(key=len) # Shortest path to an edge
                self.current_path = paths_to_edge_frontiers[0]
                target_coord = self.current_path[-1]
                self.message_log.add_message(f"AI: Pathing to edge of known area at ({target_coord[0]},{target_coord[1]}) to explore fog.")
                target_type_sought = "edge of fog"
                return

        self.message_log.add_message(f"AI: No {target_type_sought} found to explore on visible map.")
        # If current_path is still None here, get_next_action will handle it (e.g. look around)


    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        """
        Determines the next action for the AI-controlled player.
        Uses self.ai_visible_map for decisions.
        Prioritizes: winning, healing, attacking, looting, then pathfinding/exploration.
        """
        # CRITICAL: Update AI's vision before making any decisions
        self.update_visibility() # This ensures ai_visible_map is up-to-date

        current_player_pos = (self.player.x, self.player.y)
        # Add current position to physically visited coordinates
        if current_player_pos not in self.physically_visited_coords:
            self.physically_visited_coords.append(current_player_pos)

        # Decisions should be based on ai_visible_map
        current_tile_on_visible_map = self.ai_visible_map.get_tile(current_player_pos[0], current_player_pos[1])

        # 1. Winning Condition (on current tile, based on visible map)
        if (
            current_tile_on_visible_map and current_tile_on_visible_map.is_explored
            and current_tile_on_visible_map.item
            and current_tile_on_visible_map.item.properties.get("type") == "quest"
        ):
            self.message_log.add_message(
                f"AI: Found quest item {current_tile_on_visible_map.item.name}!"
            )
            self.current_path = None
            return ("take", current_tile_on_visible_map.item.name)

        # 2. Use Potion if Low Health (from inventory)
        low_health_threshold = self.player.max_health * 0.5
        if self.player.health < low_health_threshold:
            health_potion_inv = next((item for item in self.player.inventory if "health potion" in item.name.lower() and item.properties.get("type") == "heal"), None)
            if health_potion_inv:
                self.message_log.add_message("AI: Low health, using Health Potion from inventory.")
                self.current_path = None
                return ("use", health_potion_inv.name)
            # If no potion in inventory, _find_target_and_path will prioritize finding one if visible

        # 3. Take Other Items (non-quest, on current tile, based on visible map)
        if current_tile_on_visible_map and current_tile_on_visible_map.is_explored and current_tile_on_visible_map.item:
            # Check if it's a health potion and if health is full
            item_is_potion = "health potion" in current_tile_on_visible_map.item.name.lower() and \
                             current_tile_on_visible_map.item.properties.get("type") == "heal"
            if item_is_potion and self.player.health >= self.player.max_health:
                self.message_log.add_message(f"AI: On tile with {current_tile_on_visible_map.item.name}, but health is full. Skipping.")
            else:
                self.message_log.add_message(
                    f"AI: Found item {current_tile_on_visible_map.item.name} on current tile, taking it."
                )
                self.current_path = None
                return ("take", current_tile_on_visible_map.item.name)

        # 4. Attack Adjacent Monsters (based on visible map)
        adjacent_monsters = self._get_adjacent_monsters() # This now uses ai_visible_map
        if adjacent_monsters:
            monster_to_attack = random.choice(adjacent_monsters)
            self.message_log.add_message(f"AI: Attacking adjacent {monster_to_attack.name}.")
            self.current_path = None
            return ("attack", monster_to_attack.name)

        # 5. Follow Current Path or Find New Path (using ai_visible_map)
        if self.current_path:
            if self.current_path[0] == current_player_pos:
                self.current_path.pop(0)

            if not self.current_path:
                self.current_path = None
            else:
                next_step_pos = self.current_path[0]
                next_tile_visible = self.ai_visible_map.get_tile(next_step_pos[0], next_step_pos[1])

                # Path validation should use ai_visible_map and its is_explored status
                # A tile is valid to move to if it's explored and not a wall, and no monster (unless target)
                can_move_to_next_step = False
                if next_tile_visible and next_tile_visible.is_explored:
                    if next_tile_visible.type != "wall":
                        if next_tile_visible.monster:
                            # Allow stepping on monster only if it's the final destination of the path
                            if next_step_pos == self.current_path[-1]:
                                can_move_to_next_step = True
                            # else: path blocked by unexpected monster
                        else:
                            can_move_to_next_step = True

                if not can_move_to_next_step:
                    self.message_log.add_message("AI: Path blocked on visible map, recalculating.")
                    self.current_path = None
                else:
                    move_command = self._coordinates_to_move_command(
                        current_player_pos, next_step_pos
                    )
                    if move_command:
                        self.message_log.add_message(
                            f"AI: Following path on visible map. Moving {move_command[1]} to ({next_step_pos[0]},{next_step_pos[1]})."
                        )
                        self.last_move_command = move_command
                        return move_command
                    else:
                        self.message_log.add_message("AI: Error in path following (visible map), recalculating.")
                        self.current_path = None

        if not self.current_path:
            self._find_target_and_path() # This now uses ai_visible_map and new priority
            if self.current_path:
                if self.current_path[0] == current_player_pos: # Path might start with current
                    self.current_path.pop(0)

                if not self.current_path: # Path was just to current location
                     self.message_log.add_message("AI: New path target is current location (visible map). Looking around.")
                     self.last_move_command = ("look", None)
                     return ("look", None)

                next_step_pos = self.current_path[0]
                move_command = self._coordinates_to_move_command(
                    current_player_pos, next_step_pos
                )
                if move_command:
                    next_tile_visible = self.ai_visible_map.get_tile(next_step_pos[0], next_step_pos[1])
                    can_move_to_first_step = False
                    if next_tile_visible and next_tile_visible.is_explored:
                        if next_tile_visible.type != "wall":
                            if next_tile_visible.monster:
                                if next_step_pos == self.current_path[-1]: # It's the target monster
                                    can_move_to_first_step = True
                            else: # No monster
                                can_move_to_first_step = True

                    if not can_move_to_first_step:
                        self.message_log.add_message("AI: First step of new path blocked (visible map). Looking around.")
                        self.current_path = None
                        self.last_move_command = ("look", None)
                        return ("look", None)

                    self.message_log.add_message(
                        f"AI: Starting new path (visible map). Moving {move_command[1]} to ({next_step_pos[0]},{next_step_pos[1]})."
                    )
                    self.last_move_command = move_command
                    return move_command
                else:
                    self.message_log.add_message("AI: Error in new path step (visible map). Looking around.")
                    self.current_path = None
                    self.last_move_command = ("look", None)
                    return ("look", None)

        self.message_log.add_message("AI: No path found on visible map and no other actions. Looking around.")
        self.last_move_command = ("look", None)
        return ("look", None)

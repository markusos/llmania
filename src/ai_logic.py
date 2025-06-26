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
        self, player: "Player", world_map: "WorldMap", message_log: "MessageLog"
    ):
        """
        Initializes the AILogic system.

        Args:
            player: The player object that the AI will control.
            world_map: The game world map.
            message_log: The message log for recording actions or observations.
        """
        self.player = player
        self.world_map = world_map
        self.message_log = message_log
        self.path_finder = PathFinder()
        self.visited_tiles: List[Tuple[int, int]] = []
        self.current_path: Optional[List[Tuple[int, int]]] = None
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None # Keep for simple move tracking

    def _get_adjacent_monsters(self) -> List["Monster"]:
        """
        Checks N, S, E, W tiles around the player for monsters.
        """
        adjacent_monsters: List["Monster"] = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # N, S, W, E
            check_x, check_y = self.player.x + dx, self.player.y + dy
            tile = self.world_map.get_tile(check_x, check_y)
            if tile and tile.monster:
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

        potential_targets: List[Tuple[int, int]] = []
        target_type_sought = "any" # For logging

        # 1. Quest Item
        for y in range(self.world_map.height):
            for x in range(self.world_map.width):
                tile = self.world_map.get_tile(x, y)
                if (
                    tile
                    and tile.item
                    and tile.item.properties.get("type") == "quest"
                ):
                    path = self.path_finder.find_path_bfs(
                        self.world_map, player_pos, (x, y)
                    )
                    if path:
                        self.message_log.add_message(f"AI: Pathing to quest item at ({x},{y}).")
                        self.current_path = path
                        return

        # 2. Other Items
        items_coords: List[Tuple[int,int]] = []
        for y in range(self.world_map.height):
            for x in range(self.world_map.width):
                tile = self.world_map.get_tile(x, y)
                if tile and tile.item and (x,y) != player_pos : # Don't target item on current tile via pathing
                    items_coords.append((x,y))

        if items_coords:
            paths_to_items = []
            for coord in items_coords:
                path = self.path_finder.find_path_bfs(self.world_map, player_pos, coord)
                if path:
                    paths_to_items.append(path)

            if paths_to_items:
                paths_to_items.sort(key=len)
                self.current_path = paths_to_items[0]
                target_coord = self.current_path[-1]
                self.message_log.add_message(f"AI: Pathing to item at ({target_coord[0]},{target_coord[1]}).")
                target_type_sought = "item"
                return

        # 3. Monsters (not adjacent)
        monster_coords: List[Tuple[int,int]] = []
        for y in range(self.world_map.height):
            for x in range(self.world_map.width):
                tile = self.world_map.get_tile(x, y)
                if tile and tile.monster:
                    is_adjacent = False
                    for dx_adj, dy_adj in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        if player_pos[0] + dx_adj == x and player_pos[1] + dy_adj == y:
                            is_adjacent = True
                            break
                    if not is_adjacent:
                         monster_coords.append((x,y))

        if monster_coords:
            paths_to_monsters = []
            for coord in monster_coords:
                path = self.path_finder.find_path_bfs(self.world_map, player_pos, coord)
                if path:
                    paths_to_monsters.append(path)

            if paths_to_monsters:
                paths_to_monsters.sort(key=len)
                self.current_path = paths_to_monsters[0]
                target_coord = self.current_path[-1]
                self.message_log.add_message(f"AI: Pathing to monster at ({target_coord[0]},{target_coord[1]}).")
                target_type_sought = "monster"
                return

        # 4. Unvisited Tiles
        unvisited_coords: List[Tuple[int,int]] = []
        for y in range(self.world_map.height):
            for x in range(self.world_map.width):
                if (x, y) not in self.visited_tiles:
                    tile = self.world_map.get_tile(x,y)
                    if tile and tile.type != "wall": # Ensure it's potentially pathable
                        unvisited_coords.append((x,y))

        if unvisited_coords:
            # Sort unvisited tiles by path distance
            # This can be computationally expensive if many unvisited tiles.
            # Consider limiting the number of tiles to pathfind to, or using a simpler heuristic.
            # For now, full sort.
            paths_to_unvisited = []
            for coord in unvisited_coords:
                path = self.path_finder.find_path_bfs(self.world_map, player_pos, coord)
                if path:
                    paths_to_unvisited.append(path)

            if paths_to_unvisited:
                paths_to_unvisited.sort(key=len)
                self.current_path = paths_to_unvisited[0]
                target_coord = self.current_path[-1]
                self.message_log.add_message(f"AI: Pathing to unvisited tile at ({target_coord[0]},{target_coord[1]}).")
                target_type_sought = "unvisited tile"
                return

        self.message_log.add_message(f"AI: No pathable {target_type_sought} found to explore.")


    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        """
        Determines the next action for the AI-controlled player.
        Prioritizes winning, healing, attacking, looting, then pathfinding/exploration.
        """
        current_player_pos = (self.player.x, self.player.y)
        current_tile = self.world_map.get_tile(current_player_pos[0], current_player_pos[1])

        # Update visited tiles
        if current_player_pos not in self.visited_tiles:
            self.visited_tiles.append(current_player_pos)

        # 1. Winning Condition (on current tile)
        if (
            current_tile
            and current_tile.item
            and current_tile.item.properties.get("type") == "quest"
        ):
            self.message_log.add_message(
                f"AI: Found quest item {current_tile.item.name}!"
            )
            self.current_path = None # Clear path after achieving goal
            return ("take", current_tile.item.name)

        # 2. Use Potion if Low Health
        low_health_threshold = self.player.max_health * 0.5  # Example: 50% health
        if self.player.health < low_health_threshold:
            # Search for "Health Potion" more robustly
            health_potion = next((item for item in self.player.inventory if "health potion" in item.name.lower() and item.properties.get("type") == "heal"), None)
            if health_potion:
                self.message_log.add_message("AI: Low health, using Health Potion.")
                self.current_path = None # Action taken, might need new path
                return ("use", health_potion.name)


        # 3. Take Other Items (non-quest, on current tile)
        if current_tile and current_tile.item: # Quest item handled above
            self.message_log.add_message(
                f"AI: Found item {current_tile.item.name}, taking it."
            )
            self.current_path = None # Clear path after taking item
            return ("take", current_tile.item.name)

        # 4. Attack Adjacent Monsters
        adjacent_monsters = self._get_adjacent_monsters()
        if adjacent_monsters:
            monster_to_attack = random.choice(adjacent_monsters) # Attack a random adjacent one
            self.message_log.add_message(f"AI: Attacking {monster_to_attack.name}.")
            self.current_path = None # Attacking, clear path
            return ("attack", monster_to_attack.name)

        # 5. Follow Current Path or Find New Path
        if self.current_path:
            # Remove current player position from path if it's the first step
            if self.current_path[0] == current_player_pos:
                self.current_path.pop(0)

            if not self.current_path: # Path completed or was just current pos
                self.current_path = None
                # Fall through to find new path
            else:
                next_step_pos = self.current_path[0]
                # Validate next step (e.g. if a monster moved into the path)
                next_tile = self.world_map.get_tile(next_step_pos[0], next_step_pos[1])
                if not self.world_map.is_valid_move(next_step_pos[0], next_step_pos[1]) or \
                   (next_tile and next_tile.monster and next_step_pos != self.current_path[-1]): # Don't step on monster unless it's the target
                    self.message_log.add_message("AI: Path blocked, recalculating.")
                    self.current_path = None # Path is blocked
                    # Fall through to find new path
                else:
                    move_command = self._coordinates_to_move_command(
                        current_player_pos, next_step_pos
                    )
                    if move_command:
                        self.message_log.add_message(
                            f"AI: Following path. Moving {move_command[1]} to ({next_step_pos[0]},{next_step_pos[1]})."
                        )
                        self.last_move_command = move_command
                        return move_command
                    else: # Should not happen if path has valid adjacent steps
                        self.message_log.add_message("AI: Error in path following, recalculating.")
                        self.current_path = None


        # If no current path, or path was invalidated/completed, find a new one
        if not self.current_path:
            self._find_target_and_path()
            # After finding a new path, try to take the first step in the same turn
            if self.current_path:
                # Remove current player position if it's the start of the new path
                if self.current_path[0] == current_player_pos:
                    self.current_path.pop(0)

                if not self.current_path: # Path was just to current location
                     self.message_log.add_message("AI: New path target is current location. Looking around.")
                     self.last_move_command = ("look", None)
                     return ("look", None)

                next_step_pos = self.current_path[0]
                move_command = self._coordinates_to_move_command(
                    current_player_pos, next_step_pos
                )
                if move_command:
                    # Validate this first step immediately
                    next_tile = self.world_map.get_tile(next_step_pos[0], next_step_pos[1])
                    if not self.world_map.is_valid_move(next_step_pos[0], next_step_pos[1]) or \
                       (next_tile and next_tile.monster and next_step_pos != self.current_path[-1]):
                        self.message_log.add_message("AI: First step of new path blocked. Looking around.")
                        self.current_path = None
                        self.last_move_command = ("look", None)
                        return ("look", None)

                    self.message_log.add_message(
                        f"AI: Starting new path. Moving {move_command[1]} to ({next_step_pos[0]},{next_step_pos[1]})."
                    )
                    self.last_move_command = move_command
                    return move_command
                else: # Error converting coordinates
                    self.message_log.add_message("AI: Error in new path step. Looking around.")
                    self.current_path = None # Invalidate path
                    self.last_move_command = ("look", None)
                    return ("look", None)

        # If no path found and no other actions
        self.message_log.add_message("AI: No path found and no other actions. Looking around.")
        self.last_move_command = ("look", None)
        return ("look", None)

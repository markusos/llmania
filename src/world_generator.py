import random
from collections import deque
from typing import Optional

from src.item import Item
from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.density import FloorDensityAdjuster
from src.map_algorithms.pathfinding import PathFinder
from src.monster import Monster
from src.world_map import WorldMap


class WorldGenerator:
    """
    Generates the game world, including multiple floors, map layouts,
    player starting position, the goal item's location, portals, and
    placement of other items and monsters.
    the goal item's location, and placement of other items and monsters.
    """

    DEFAULT_FLOOR_PORTION = 0.5

    def __init__(self, floor_portion: Optional[float] = None):
        """
        Initializes the WorldGenerator.

        Args:
            floor_portion: Optional. The desired proportion of floor tiles in the map.
                           If None, DEFAULT_FLOOR_PORTION is used.
        """
        self.floor_portion = (
            floor_portion if floor_portion is not None else self.DEFAULT_FLOOR_PORTION
        )
        self.connectivity_manager = MapConnectivityManager()
        self.density_adjuster = FloorDensityAdjuster(self.connectivity_manager)
        self.path_finder = PathFinder()

    def _get_quadrant_bounds(
        self, quadrant_index: int, map_width: int, map_height: int
    ) -> tuple[int, int, int, int]:
        """
        Calculates the (min_x, min_y, max_x, max_y) coordinates for a given quadrant.
        Quadrants: 0 for NE, 1 for SE, 2 for SW, 3 for NW.
        Ensures bounds are within the inner map area (1 to width-2, 1 to height-2).
        """
        mid_x = map_width // 2
        mid_y = map_height // 2

        # Inner map boundaries
        inner_min_x, inner_min_y = 1, 1
        inner_max_x, inner_max_y = map_width - 2, map_height - 2

        if quadrant_index == 0:  # Northeast
            min_x, min_y = mid_x, inner_min_y
            max_x, max_y = inner_max_x, mid_y - 1
        elif quadrant_index == 1:  # Southeast
            min_x, min_y = mid_x, mid_y
            max_x, max_y = inner_max_x, inner_max_y
        elif quadrant_index == 2:  # Southwest
            min_x, min_y = inner_min_x, mid_y
            max_x, max_y = mid_x - 1, inner_max_y
        elif quadrant_index == 3:  # Northwest
            min_x, min_y = inner_min_x, inner_min_y
            max_x, max_y = mid_x - 1, mid_y - 1
        else:
            raise ValueError(f"Invalid quadrant_index: {quadrant_index}")

        # Clamp to inner map boundaries to prevent issues with small maps
        # and ensure results are always valid for indexing inner map parts.
        min_x = max(inner_min_x, min_x)
        min_y = max(inner_min_y, min_y)
        max_x = min(inner_max_x, max_x)
        max_y = min(inner_max_y, max_y)

        # Ensure min <= max for degenerate cases (e.g. very small maps)
        if min_x > max_x:
            max_x = min_x
        if min_y > max_y:
            max_y = min_y

        return min_x, min_y, max_x, max_y

    def _initialize_map(self, width: int, height: int, seed: Optional[int]) -> WorldMap:
        """
        Initializes a new WorldMap. Outermost layer is "wall", inner tiles
        are "potential_floor". Initializes RNG if seed is provided.

        Args:
            width: The width of the map.
            height: The height of the map.
            seed: An optional seed for the random number generator.

        Returns:
            A WorldMap instance.
        """
        if seed is not None:
            # Initialize RNG for deterministic generation if seed is given
            random.seed(seed)

        world_map = WorldMap(width, height)
        # Set tiles: outer layer wall, inner potential_floor
        for y in range(height):
            for x in range(width):
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    world_map.set_tile_type(x, y, "wall")
                else:
                    world_map.set_tile_type(x, y, "potential_floor")
        return world_map

    def _select_start_and_win_positions(
        self, width: int, height: int, world_map: WorldMap
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Selects random starting positions for the player and the goal (win condition).
        Ensures these positions are not at the very edge of the map if possible,
        and that they are different from each other if the map is larger than 1x1.
        Sets these positions to "floor" on the map.

        Args:
            width: The width of the map.
            height: The height of the map.
            world_map: The WorldMap instance to modify.

        Returns:
            A tuple containing (player_start_pos, original_win_pos).
        Raises:
            ValueError: If dimensions are too small for valid "potential_floor"
                        tiles for start/win positions (min 3x4 or 4x3).
        """
        if (width < 3 or height < 4) and (width < 4 or height < 3):
            raise ValueError(
                "Map dimensions must be at least 3x4 or 4x3 to select "
                "start/win positions from 'potential_floor' tiles."
            )

        # Select player start and win positions from the inner "potential_floor"
        # area. Examples:
        # 3x4 map: inner width=1, height=2. random.randint(1,1) and
        # random.randint(1,2) are valid.
        # 4x3 map: inner width=2, height=1. random.randint(1,2) and
        # random.randint(1,1) are valid.
        player_start_x = random.randint(1, width - 2)
        player_start_y = random.randint(1, height - 2)
        win_x = random.randint(1, width - 2)
        win_y = random.randint(1, height - 2)

        player_start_pos = (player_start_x, player_start_y)
        original_win_pos = (win_x, win_y)

        # Ensure win_pos is different from player_start_pos, if possible.
        # For a 3x3 map (1 inner cell), they will be the same.
        attempts = 0
        # Max attempts heuristic: half the number of potential_floor cells.
        max_attempts = ((width - 2) * (height - 2)) // 2 + 1
        if max_attempts <= 0:
            max_attempts = 1  # Ensure at least one attempt for tiny areas.

        while original_win_pos == player_start_pos:
            if attempts >= max_attempts:
                # This case is rare in maps 3x3 or larger.
                # If the inner area is just one cell (3x3 map), and player_start
                # is that cell, this loop implies we must find a different spot.
                # This would be an infinite loop if not handled.
                if (width - 2) * (height - 2) == 1:  # Single inner cell
                    break  # No other choice for original_win_pos
                # For larger maps, exhausting attempts is unexpected.
                # It might occur if random.randint is not behaving ideally or
                # max_attempts is too low. For simplicity, allow same positions.
                # A more robust method might iterate all possible spots.
                break
            win_x = random.randint(1, width - 2)
            win_y = random.randint(1, height - 2)
            original_win_pos = (win_x, win_y)
            attempts += 1

        # Set the selected positions to be floor tiles
        world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
        world_map.set_tile_type(original_win_pos[0], original_win_pos[1], "floor")
        return player_start_pos, original_win_pos

    # _ensure_all_tiles_accessible was moved to
    # MapConnectivityManager.ensure_connectivity
    # _carve_path was moved to PathFinder.carve_bresenham_line

    def _get_random_tile_in_bounds(
        self,
        world_map: WorldMap,
        bounds: tuple[int, int, int, int],
        tile_type: str,
        max_attempts: int = 100,
    ) -> Optional[tuple[int, int]]:
        """
        Searches for a random tile of `tile_type` within the given `bounds`.
        Makes `max_attempts` to find such a tile.
        Returns `(x, y)` if found, else `None`.
        """
        min_x, min_y, max_x, max_y = bounds
        if min_x > max_x or min_y > max_y:  # Check if bounds are valid
            return None

        for _ in range(max_attempts):
            # Ensure random.randint arguments are valid (low <= high)
            if max_x < min_x or max_y < min_y:  # Should not happen if bounds are valid
                return None  # Or handle as an error/log

            rand_x = random.randint(min_x, max_x)
            rand_y = random.randint(min_y, max_y)

            tile = world_map.get_tile(rand_x, rand_y)
            if tile and tile.type == tile_type:
                return rand_x, rand_y
        return None

    def _perform_directed_random_walk(
        self,
        world_map: WorldMap,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        map_width: int,
        map_height: int,
        # max_steps: int = 75, # Default is now dynamically set based on floor_portion
    ):
        """
        Performs a directed random walk from start_pos towards end_pos,
        with a bias towards continuing in the same direction.
        Length of walk depends on self.floor_portion.
        Now includes backtracking to avoid creating isolated areas.
        """
        current_x, current_y = start_pos
        world_map.set_tile_type(current_x, current_y, "floor")  # Carve start_pos

        last_dx, last_dy = 0, 0  # Initialize last direction

        current_walk_max_steps = 75
        if self.floor_portion < 0.35:
            current_walk_max_steps = 40  # Shorter walks for low target density

        # Keep track of the path to enable backtracking
        path_history = [(current_x, current_y)]
        stuck_count = 0
        max_stuck_attempts = 5

        for step in range(current_walk_max_steps):
            if (current_x, current_y) == end_pos:
                break

            dx = end_pos[0] - current_x
            dy = end_pos[1] - current_y

            possible_directions = []
            # Check all four directions
            for direction_dx, direction_dy, direction_name in [
                (0, -1, "N"),
                (0, 1, "S"),
                (-1, 0, "W"),
                (1, 0, "E"),
            ]:
                new_x, new_y = current_x + direction_dx, current_y + direction_dy
                if 1 <= new_x < map_width - 1 and 1 <= new_y < map_height - 1:
                    possible_directions.append(
                        (direction_dx, direction_dy, direction_name)
                    )

            if not possible_directions:
                break

            # Calculate preferred directions based on target
            preferred_directions = []
            if dy < 0:  # North
                preferred_directions.append((0, -1, "N"))
            if dy > 0:  # South
                preferred_directions.append((0, 1, "S"))
            if dx < 0:  # West
                preferred_directions.append((-1, 0, "W"))
            if dx > 0:  # East
                preferred_directions.append((1, 0, "E"))

            # Filter to only valid moves
            possible_moves_set = {(d[0], d[1]) for d in possible_directions}
            preferred_directions = [
                pd
                for pd in preferred_directions
                if (pd[0], pd[1]) in possible_moves_set
            ]

            # Choose direction with 75% preference for target direction
            if preferred_directions and random.random() < 0.75:
                chosen_dx, chosen_dy, _ = random.choice(preferred_directions)
            else:  # Pick any allowed direction
                if not possible_directions:
                    break  # Should not happen if map is >1x1 inner
                chosen_dx, chosen_dy, _ = random.choice(possible_directions)

            # Introduce inertia: bias towards continuing in the last direction
            if last_dx != 0 or last_dy != 0:  # If there was a previous move
                # Check if last direction is still possible
                is_last_direction_possible = False
                for pdx, pdy, _ in possible_directions:
                    if pdx == last_dx and pdy == last_dy:
                        is_last_direction_possible = True
                        break

                # Restored to 60% chance
                if is_last_direction_possible and random.random() < 0.6:
                    chosen_dx, chosen_dy = last_dx, last_dy

            next_x, next_y = current_x + chosen_dx, current_y + chosen_dy

            # Update last direction
            last_dx, last_dy = chosen_dx, chosen_dy

            # Always move and carve the tile
            tile = world_map.get_tile(next_x, next_y)
            if tile and (tile.type == "wall" or tile.type == "potential_floor"):
                world_map.set_tile_type(next_x, next_y, "floor")

            current_x, current_y = next_x, next_y
            path_history.append((current_x, current_y))

            # Reset stuck counter when we make progress
            if len(path_history) > 1 and (current_x, current_y) != path_history[-2]:
                stuck_count = 0
            else:
                stuck_count += 1

            # If we're stuck, backtrack
            if stuck_count >= max_stuck_attempts and len(path_history) > 1:
                # Backtrack to a previous position
                backtrack_steps = min(3, len(path_history) - 1)
                for _ in range(backtrack_steps):
                    if len(path_history) > 1:
                        path_history.pop()
                if path_history:
                    current_x, current_y = path_history[-1]
                stuck_count = 0

    def _perform_random_walks(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],  # Keep for fallback
        map_width: int,
        map_height: int,
    ) -> None:
        """
        Performs quadrant-based directed random walks to carve out floor space.
        Each walk starts from a random wall tile in a quadrant and moves towards
        a random existing floor tile or the player start position.

        Args:
            world_map: The WorldMap instance to modify.
            player_start_pos: Player's starting position, used as a fallback target.
            map_width: The width of the map.
            map_height: The height of the map.
        """
        num_quadrant_paths = 4  # Restored to 4 for better coverage

        for quadrant_index in range(num_quadrant_paths):
            # actual_quadrant_index logic removed, quadrant_index directly used.
            quadrant_bounds = self._get_quadrant_bounds(
                quadrant_index, map_width, map_height
            )

            # Ensure bounds are valid before attempting to find start_node
            q_min_x, q_min_y, q_max_x, q_max_y = quadrant_bounds
            if q_min_x > q_max_x or q_min_y > q_max_y:
                # This can happen if the map is too small for the quadrant logic
                # (e.g., a 3x3 map would have degenerate quadrants).
                # Skip this quadrant or handle as appropriate.
                continue

            start_node = self._get_random_tile_in_bounds(
                world_map, quadrant_bounds, "wall"
            )

            if start_node is None:
                # Could not find a 'wall' tile in this quadrant.
                # Might happen if quadrant is fully carved/small.
                # Try to find a 'potential_floor' tile instead, or just continue.
                start_node = self._get_random_tile_in_bounds(
                    world_map, quadrant_bounds, "potential_floor"
                )
                if start_node is None:
                    # Skip to the next quadrant if no suitable start tile
                    continue

            # start_node is carved to floor in _perform_directed_random_walk

            all_floor_tiles = self._collect_floor_tiles(
                world_map, map_width, map_height
            )

            if not all_floor_tiles:
                end_node = player_start_pos  # Fallback if no floor tiles exist yet
            # (should be rare after initial setup)
            else:
                end_node = random.choice(all_floor_tiles)

            # Ensure end_node is not the same as start_node if possible
            if end_node == start_node and len(all_floor_tiles) > 1:
                potential_end_nodes = [fn for fn in all_floor_tiles if fn != start_node]
                if potential_end_nodes:
                    end_node = random.choice(potential_end_nodes)

            self._perform_directed_random_walk(
                world_map, start_node, end_node, map_width, map_height
            )

    def _generate_path_network(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],
        original_win_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> None:
        """
        Generates a network of additional paths from existing floor areas to
        random "potential_floor" tiles, expanding connectivity.
        Number of paths depends on self.floor_portion and map size.
        """
        min_paths, max_paths = 0, 0
        base_sum = map_width + map_height

        if self.floor_portion < 0.35:
            # Fewer paths for low density maps
            min_paths = 1
            # Ensure max_paths is at least min_paths
            max_paths = max(min_paths, base_sum // 10)
        else:
            # More paths for higher density and larger maps
            min_paths = max(1, base_sum // 10)
            max_paths = max(min_paths, base_sum // 5)

        num_additional_paths = random.randint(min_paths, max_paths)

        potential_target_tiles = []
        for y in range(1, map_height - 1):
            for x in range(1, map_width - 1):
                tile = world_map.get_tile(x, y)
                if tile and tile.type == "potential_floor":
                    potential_target_tiles.append((x, y))

        # Remove player_start_pos and original_win_pos from potential targets
        if player_start_pos in potential_target_tiles:
            potential_target_tiles.remove(player_start_pos)
        if original_win_pos in potential_target_tiles:
            potential_target_tiles.remove(original_win_pos)

        for _ in range(num_additional_paths):
            if not potential_target_tiles:
                break  # No more potential targets

            target_pos_index = random.randrange(len(potential_target_tiles))
            target_pos = potential_target_tiles.pop(target_pos_index)

            current_floor_tiles = self._collect_floor_tiles(
                world_map, map_width, map_height
            )
            if not current_floor_tiles:
                origin_pos = player_start_pos  # Fallback
            else:
                origin_pos = random.choice(current_floor_tiles)

            self.path_finder.carve_bresenham_line(
                world_map, origin_pos, target_pos, map_width, map_height
            )

    def _collect_floor_tiles(  # This method remains in WorldGenerator
        self, world_map: WorldMap, map_width: int, map_height: int
    ) -> list[tuple[int, int]]:
        """
        Scans the inner map area for "floor" tiles and returns their coordinates.

        Args:
            world_map: The WorldMap to scan.
            map_width: The width of the map.
            map_height: The height of the map.

        Returns:
            A list of (x,y) tuples representing inner floor tile coordinates.
        """
        floor_tiles = []
        # Iterate only over inner tiles, as outer border is wall and
        # all gameplay area is expected to be within this inner region.
        for y_coord in range(1, map_height - 1):
            for x_coord in range(1, map_width - 1):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "floor":
                    floor_tiles.append((x_coord, y_coord))
        return floor_tiles

    # _is_connected was moved to MapConnectivityManager.check_connectivity
    # _adjust_floor_density was moved to FloorDensityAdjuster.adjust_density
    # _find_furthest_reachable_tile was moved to PathFinder.find_furthest_point

    def _place_win_item_at_furthest_point(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],
        map_width: int,
        map_height: int,
        floor_tiles: list[tuple[int, int]],  # Used for fallback, primary logic uses BFS
    ) -> tuple[int, int]:
        """
        Places the goal item ("Amulet of Yendor") at the floor tile furthest
        reachable from player_start_pos.

        Args:
            world_map: The WorldMap instance.
            player_start_pos: The player's starting position.
            map_width: The width of the map.
            map_height: The height of the map.
            floor_tiles: A list of inner floor tile coordinates for fallback.

        Returns:
            The (x,y) coordinates where the goal item was placed.
        """
        goal_item = Item(
            "Amulet of Yendor", "The object of your quest!", {"type": "quest"}
        )

        if not floor_tiles:  # Should ideally not happen if map generation is robust
            actual_win_pos = player_start_pos
            # Ensure the fallback position is floor
            player_start_tile = world_map.get_tile(
                player_start_pos[0], player_start_pos[1]
            )
            if not player_start_tile or player_start_tile.type != "floor":
                world_map.set_tile_type(
                    player_start_pos[0], player_start_pos[1], "floor"
                )
        else:
            actual_win_pos = self.path_finder.find_furthest_point(
                world_map, player_start_pos, map_width, map_height
            )
            # Fallback if find_furthest_point returns a non-floor or invalid tile
            chosen_tile = world_map.get_tile(actual_win_pos[0], actual_win_pos[1])
            if not chosen_tile or chosen_tile.type != "floor":
                # Prefer a floor tile different from player_start_pos
                available_goal_spots = [
                    tile for tile in floor_tiles if tile != player_start_pos
                ]
                if available_goal_spots:
                    actual_win_pos = random.choice(available_goal_spots)
                elif player_start_pos in floor_tiles:  # Only player_start_pos is floor
                    actual_win_pos = player_start_pos
                else:  # Should be extremely rare: no floor tiles,
                    # player_start_pos invalid.
                    # Default to player_start_pos and make it floor.
                    actual_win_pos = player_start_pos
                    world_map.set_tile_type(
                        player_start_pos[0], player_start_pos[1], "floor"
                    )

        world_map.place_item(goal_item, actual_win_pos[0], actual_win_pos[1])
        return actual_win_pos

    def _place_additional_entities(
        self,
        world_map: WorldMap,
        floor_tiles: list[tuple[int, int]],
        player_start_pos: tuple[int, int],
        actual_win_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> None:
        """
        Places additional items (potions, daggers) and monsters (goblins, bats)
        randomly on available floor tiles. Avoids player's start and win positions.

        Args:
            world_map: The WorldMap instance.
            floor_tiles: A list of all floor tile coordinates.
            player_start_pos: The player's starting position.
            actual_win_pos: The actual position of the goal item.
            map_width: The width of the map.
            map_height: The height of the map.
        """
        if not floor_tiles:  # No floor tiles to place entities on.
            return

        # Determine number of entities to try placing based on map size.
        num_placements = (map_width * map_height) // 15  # Example density

        # Filter floor_tiles to get spots available for random entities.
        # Exclude player start and the goal item's location.
        available_floor_tiles_for_entities = [
            tile
            for tile in floor_tiles
            if tile != player_start_pos and tile != actual_win_pos
        ]

        for _ in range(num_placements):
            if not available_floor_tiles_for_entities:  # No more valid spots
                break

            # Choose random available tile and remove it from list for unique placement.
            chosen_tile_index = random.randrange(
                len(available_floor_tiles_for_entities)
            )
            chosen_tile_pos = available_floor_tiles_for_entities.pop(chosen_tile_index)

            # Check if chosen tile is empty (should be, as picked from available floor).
            tile_obj = world_map.get_tile(chosen_tile_pos[0], chosen_tile_pos[1])
            if tile_obj and tile_obj.item is None and tile_obj.monster is None:
                # Decide whether to place an item or a monster
                if random.random() < 0.15:  # 15% chance to place an item
                    # Randomly choose between a health potion and a dagger
                    if random.random() < 0.5:
                        item_to_place = Item(
                            "Health Potion",
                            "Restores some HP.",
                            {"type": "heal", "amount": 10},
                        )
                    else:
                        item_to_place = Item(
                            "Dagger",
                            "A small blade.",
                            {"type": "weapon", "attack_bonus": 2, "verb": "stabs"},
                        )
                    world_map.place_item(
                        item_to_place, chosen_tile_pos[0], chosen_tile_pos[1]
                    )
                elif (
                    random.random() < 0.10
                ):  # 10% chance to place a monster (after failing item placement)
                    # Randomly choose between a goblin and a bat
                    if random.random() < 0.5:
                        monster_to_place = Monster(
                            "Goblin", 10, 3, x=chosen_tile_pos[0], y=chosen_tile_pos[1]
                        )
                    else:
                        monster_to_place = Monster(
                            "Bat", 5, 2, x=chosen_tile_pos[0], y=chosen_tile_pos[1]
                        )
                    world_map.place_monster(
                        monster_to_place, chosen_tile_pos[0], chosen_tile_pos[1]
                    )

    def _generate_single_floor( # Renamed from generate_map
        self, width: int, height: int, current_seed: int | None = None
    ) -> tuple[WorldMap, tuple[int, int], tuple[int, int]]:
        """
        Generates a single complete game map (floor) with player start, goal, paths, items,
        and monsters. Requires map dimensions to be at least 3x3.

        The process involves:
        1. Initializing a map with border walls and inner "potential_floor" tiles.
        2. Selecting player start and initial win positions, making them floor.
        3. Carving a guaranteed path between player start and win positions.
        4. Performing random walks to create more open floor areas.
        5. Collecting all floor tiles.
        6. Placing the goal item (Amulet of Yendor), potentially adjusting win position.
        7. Placing additional items and monsters on available floor tiles.

        Args:
            width: The desired width of the map.
            height: The desired height of the map.
            current_seed: Optional seed for RNG for deterministic map generation for this floor.

        Returns:
            A tuple containing:
                - world_map (WorldMap): The generated game map.
                - player_start_pos (tuple[int, int]): Player's start (x,y) coordinates on this floor.
                - actual_win_pos (tuple[int, int]): Goal item's (x,y) coordinates on this floor.
        Raises:
            ValueError: If dimensions are less than 3x4 or 4x3.
        """
        if (width < 3 or height < 4) and (width < 4 or height < 3):
            raise ValueError(
                "Map dimensions must be at least 3x4 or 4x3 for this generator."
            )
        # Use provided seed for this floor's generation if available.
        # Global seed is handled in generate_world.
        if current_seed is not None:
            random.seed(current_seed)

        # Pass None for seed to _initialize_map, as it's handled here or globally.
        world_map = self._initialize_map(width, height, None)

        # These start/win positions guide this specific floor's generation.
        # Actual game start/win are determined in generate_world().
        floor_start, floor_potential_win = self._select_start_and_win_positions(
            width, height, world_map
        )

        self.path_finder.carve_bresenham_line(
            world_map, floor_start, floor_potential_win, width, height
        )
        self._perform_random_walks(world_map, floor_start, width, height)
        self._generate_path_network(
            world_map, floor_start, floor_potential_win, width, height
        )

        # Convert remaining "potential_floor" to "wall" before density adjustment.
        for y_coord in range(1, height - 1):
            for x_coord in range(1, width - 1):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "potential_floor":
                    world_map.set_tile_type(x_coord, y_coord, "wall")

        self.density_adjuster.adjust_density(
            world_map,
            floor_start,
            floor_potential_win,
            width, height, self.floor_portion,
        )

        self.connectivity_manager.ensure_connectivity(
            world_map, floor_start, width, height
        )

        # Verify all floor tiles are reachable.
        floor_tiles = self._collect_floor_tiles(world_map, width, height)
        if len(floor_tiles) > 1:
            reachable_tiles = set()
            start_bfs_tile = world_map.get_tile(floor_start[0], floor_start[1])

            queue = deque()
            if start_bfs_tile and start_bfs_tile.type == "floor":
                queue.append(floor_start)
                reachable_tiles.add(floor_start)
            elif floor_tiles: # Fallback if floor_start isn't floor
                # This is a fallback; ideally floor_start is always valid.
                bfs_fallback_start = floor_tiles[0]
                queue.append(bfs_fallback_start)
                reachable_tiles.add(bfs_fallback_start)

            while queue:
                curr_x, curr_y = queue.popleft()
                for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                    next_x, next_y = curr_x + dx, curr_y + dy
                    if (next_x, next_y) not in reachable_tiles:
                        tile = world_map.get_tile(next_x, next_y)
                        if tile and tile.type == "floor":
                            reachable_tiles.add((next_x, next_y))
                            queue.append((next_x, next_y))

            # Convert unreachable floor tiles to walls
            for x, y in floor_tiles:
                if (x, y) not in reachable_tiles:
                    world_map.set_tile_type(x, y, "wall")

        # Collect final floor tiles for item/monster placement
        # _collect_floor_tiles remains in WorldGenerator for this purpose.
        floor_tiles = self._collect_floor_tiles(world_map, width, height)

        # Safeguard: Ensure player_start_pos and original_win_pos are floor tiles.
        # Should be guaranteed by _select_start_and_win_positions and _carve_path.
        if not floor_tiles:
            # Fallback: ensure floor_start and floor_potential_win are floor.
            world_map.set_tile_type(floor_start[0], floor_start[1], "floor")
            if floor_start not in floor_tiles:
                floor_tiles.append(floor_start)

            if floor_potential_win != floor_start or ((width-2)*(height-2) > 1) :
                world_map.set_tile_type(
                    floor_potential_win[0], floor_potential_win[1], "floor"
                )
                if floor_potential_win not in floor_tiles:
                     floor_tiles.append(floor_potential_win)

        # "Win item" (Amulet) is placed by generate_world.
        # For a single floor, _place_win_item_at_furthest_point determines a
        # "point of interest" (poi). This poi might be used for portal placement
        # or a major item if this floor isn't the final Amulet floor.
        # The actual Amulet is placed by generate_world().

        # Determine a point of interest for this floor.
        # This method currently places an "Amulet of Yendor".
        # We'll remove it afterwards as generate_world places the true one.
        poi_pos = self._place_win_item_at_furthest_point(
            world_map, floor_start, width, height, floor_tiles
        )

        # Temp: remove Amulet placed by helper, as generate_world places the real one.
        # TODO: Refactor _place_win_item_at_furthest_point to not place the item,
        # or to accept the item to be placed.
        amulet_tile = world_map.get_tile(poi_pos[0], poi_pos[1])
        if amulet_tile and amulet_tile.item and \
           amulet_tile.item.name == "Amulet of Yendor":
            world_map.remove_item(poi_pos[0], poi_pos[1])

        self._place_additional_entities(
            world_map, floor_tiles, floor_start, poi_pos, width, height
        )
        # Returned start/poi are for this floor's layout, not global game.
        return world_map, floor_start, poi_pos

    def _place_portals_on_floor(
        self,
        world_map: WorldMap,
        num_portals_to_place: int, # Currently unused, logic derives candidates
        taken_portal_coords: set[tuple[int,int]]
    ) -> list[tuple[int,int]]:
        """Identifies candidate portal locations on available floor tiles."""
        # This method primarily identifies candidates; _ensure_portal_connectivity
        # does the actual placement and linking.
        placed_portals_coords = [] # Stores (x,y) of candidates from this floor
        floor_tiles_map = self._collect_floor_tiles(
            world_map, world_map.width, world_map.height
        )

        # Filter out coords already used by portals on other floors,
        # and tiles with items.
        available_for_portal = [
            (x,y) for x,y in floor_tiles_map
            if (x,y) not in taken_portal_coords and
               world_map.get_tile(x,y) and world_map.get_tile(x,y).item is None
        ]
        random.shuffle(available_for_portal)

        # For now, let _ensure_portal_connectivity decide how many actual portals
        # are made from these candidates. This method just provides possibilities.
        # Let's return up to N candidates.
        # The num_portals_to_place argument could be used here if a fixed number
        # of candidates per floor was desired.
        # For now, we use the logic in _ensure_portal_connectivity to pick candidates.

        # This function's role is reduced to just providing a list of
        # potential (x,y) coordinates for portals on this floor.
        # The actual selection and linking is complex and better handled centrally.
        # The original intent of num_portals_to_place is somewhat superseded by the
        # candidate selection in _ensure_portal_connectivity.
        # However, we can use it as a cap on candidates from this floor.

        # Return all valid, available spots as candidates for now.
        # _ensure_portal_connectivity will then pick from these across all floors.
        # This means num_portals_to_place isn't strictly used here to limit,
        # but rather the candidate collection in _ensure_portal_connectivity does.
        # For simplicity, let's return all available spots.
        # `taken_portal_coords` is updated by the caller if a portal is actually made.

        return available_for_portal # Return all valid spots


    def _ensure_portal_connectivity(
        self,
        world_maps: dict[int, WorldMap],
        width: int,
        height: int
    ) -> None:
        """
        Ensures all floors are connected by portals.
        Places portals strategically to link floors.
        """
        num_floors = len(world_maps)
        if num_floors <= 1:
            return

        # Track which (x,y) coordinates are already used by portals on any floor
        # to maintain the same (x,y) rule for linked portals.
        taken_portal_coords: set[tuple[int,int]] = set()

        # Adjacency list for floor connectivity graph
        floor_connections: dict[int, set[int]] = {i: set() for i in range(num_floors)}

        # First pass: identify some portal candidates on each floor
        portal_coords_by_floor: dict[int, list[tuple[int,int]]] = {}

        for floor_id, current_map in world_maps.items():
            floor_tiles = self._collect_floor_tiles(current_map, width, height)
            if not floor_tiles:
                portal_coords_by_floor[floor_id] = []
                continue # Skip if floor has no floor tiles

            # Try to pick a few diverse spots for portals (max 3 candidates per floor).
            num_candidates_on_floor = min(len(floor_tiles), 3)

            candidates_on_this_floor = []
            # Portals should not overwrite items.
            available_spots = [
                (x,y) for x,y in floor_tiles
                if current_map.get_tile(x,y) and current_map.get_tile(x,y).item is None
            ]
            random.shuffle(available_spots)

            for _ in range(num_candidates_on_floor):
                if not available_spots:
                    break
                spot = available_spots.pop()
                candidates_on_this_floor.append(spot)

            portal_coords_by_floor[floor_id] = candidates_on_this_floor
            # The variable all_potential_portal_spots was here previously but removed as unused.

        # Ensure overall connectivity using Disjoint Set Union (DSU).
        parent = list(range(num_floors))
        def find(i):
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j
                return True # Merge occurred
            return False # Already in same set

        # Create initial portal pairs. Connect floor i with (i+1)%num_floors at a
        # shared available (x,y) coordinate. This needs to be robust.

        processed_portal_locations: set[tuple[int,int,int]] = set() # (floor_id, x, y)

        for i in range(num_floors):
            floor1_id = i
            floor2_id = (i + 1) % num_floors # Connect to next floor, wrap around

            if find(floor1_id) == find(floor2_id) and num_floors > 2:
                # Already connected, and other floors exist.
                # This 'pass' might lead to suboptimal connectivity.
                pass

            # Attempt to find a common, available (x,y) for a portal pair.
            coords1_candidates = portal_coords_by_floor.get(floor1_id, [])
            coords2_candidates = portal_coords_by_floor.get(floor2_id, [])

            possible_link_coords = []
            random.shuffle(coords1_candidates)

            for x_coord, y_coord in coords1_candidates:
                # Check if (x,y) is candidate on floor2 & not globally taken.
                if (x_coord, y_coord) in coords2_candidates and \
                   (x_coord, y_coord) not in taken_portal_coords:
                    possible_link_coords.append((x_coord, y_coord))

            if possible_link_coords:
                portal_x, portal_y = random.choice(possible_link_coords)

                portal_key1 = (floor1_id, portal_x, portal_y)
                portal_key2 = (floor2_id, portal_x, portal_y)

                # Ensure these specific portal instances haven't been made.
                # `taken_portal_coords` checks if (x,y) is used by ANY pair.
                # `processed_portal_locations` checks if this specific
                # (floor_id, x, y) endpoint is used.
                if portal_key1 not in processed_portal_locations and \
                   portal_key2 not in processed_portal_locations:

                    tile1 = world_maps[floor1_id].grid[portal_y][portal_x]
                    tile2 = world_maps[floor2_id].grid[portal_y][portal_x]

                    tile1.type = "portal"
                    tile1.is_portal = True
                    tile1.portal_to_floor_id = floor2_id

                    tile2.type = "portal"
                    tile2.is_portal = True
                    tile2.portal_to_floor_id = floor1_id

                    union(floor1_id, floor2_id)
                    taken_portal_coords.add((portal_x, portal_y))
                    processed_portal_locations.add(portal_key1)
                    processed_portal_locations.add(portal_key2)

                    # Add to floor_connections for graph representation
                    floor_connections[floor1_id].add(floor2_id)
                    floor_connections[floor2_id].add(floor1_id)


        # After initial pairing, check DSU. If not all connected, add more portals.
        # Count number of disjoint sets
        num_components = 0
        for i in range(num_floors):
            if parent[i] == i:
                num_components +=1

        # Attempt to connect remaining components
        connection_attempts = 0
        max_connection_attempts = num_floors * 2 # Heuristic for max attempts

        while num_components > 1 and connection_attempts < max_connection_attempts :
            connection_attempts += 1
            # Try to connect two different components
            # Pick two random floors from different components
            # floor1_id = -1 # Not needed before assignment
            # floor2_id = -1 # Not needed before assignment

            components_roots = [r for r in range(num_floors) if parent[r] == r]
            if not components_roots:
                break # Should not happen

            root1 = random.choice(components_roots)
            possible_root2 = [r for r in components_roots if r != root1]
            if not possible_root2:
                break # Only one component left

            root2 = random.choice(possible_root2)

            # Find floors belonging to these two components
            floors_in_comp1 = [f_id for f_id in range(num_floors) if find(f_id) == root1]
            floors_in_comp2 = [f_id for f_id in range(num_floors) if find(f_id) == root2]

            if not floors_in_comp1 or not floors_in_comp2:
                continue # Should not happen

            floor1_id_new_link = random.choice(floors_in_comp1)
            floor2_id_new_link = random.choice(floors_in_comp2)

            # Find a common available (x,y) for these two floors that isn't
            # globally used by another portal pair.

            # Find any unused floor tile (x,y) on floor1_id_new_link.
            # If same (x,y) is an unused floor tile on floor2_id_new_link,
            # and (x,y) is not in taken_portal_coords (i.e., not used by any
            # portal pair yet), then it's a candidate.

            potential_link_coords = []
            map1_floor_tiles = self._collect_floor_tiles(
                world_maps[floor1_id_new_link], width, height
            )
            # map2_floor_tiles is not strictly needed if we check tile on map2

            random.shuffle(map1_floor_tiles) # Shuffle to randomize choice

            for x_coord_link, y_coord_link in map1_floor_tiles:
                if (x_coord_link, y_coord_link) not in taken_portal_coords:
                    tile1_obj = world_maps[floor1_id_new_link].get_tile(x_coord_link, y_coord_link)
                    tile2_obj = world_maps[floor2_id_new_link].get_tile(x_coord_link, y_coord_link)
                    if tile1_obj and tile1_obj.type == "floor" and tile1_obj.item is None and \
                       tile2_obj and tile2_obj.type == "floor" and tile2_obj.item is None:
                        potential_link_coords.append((x_coord_link, y_coord_link))
                        break # Found one potential spot

            if potential_link_coords:
                portal_x, portal_y = potential_link_coords[0]

                tile1 = world_maps[floor1_id_new_link].grid[portal_y][portal_x]
                tile2 = world_maps[floor2_id_new_link].grid[portal_y][portal_x]

                tile1.type = "portal"
                tile1.is_portal = True
                tile1.portal_to_floor_id = floor2_id_new_link

                tile2.type = "portal"
                tile2.is_portal = True
                tile2.portal_to_floor_id = floor1_id_new_link

                union(floor1_id_new_link, floor2_id_new_link)
                taken_portal_coords.add((portal_x, portal_y))
                processed_portal_locations.add((floor1_id_new_link, portal_x, portal_y))
                processed_portal_locations.add((floor2_id_new_link, portal_x, portal_y))

                floor_connections[floor1_id_new_link].add(floor2_id_new_link)
                floor_connections[floor2_id_new_link].add(floor1_id_new_link)

                num_components = 0
                for i_comp_check in range(num_floors): # Renamed i to avoid conflict
                    if parent[i_comp_check] == i_comp_check:
                        num_components +=1
            else:
                # Could not find a common spot for these two components.
                # This might indicate map is too small or dense.
                # Or bad luck in random choices. For now, might loop or give up.
                # To prevent infinite loops if truly impossible:
                break # Break if no common coords found for this attempt.

        # Final check: if still not connected, log an error.
        final_num_components = 0
        for i_final_check in range(num_floors): # Renamed i
            if parent[i_final_check] == i_final_check:
                final_num_components +=1
        if final_num_components > 1:
            # Using print for now, consider proper logging for a library.
            print(
                f"Warning: WorldGenerator could not connect all {num_floors} floors. "
                f"{final_num_components} components remain."
            )
            # Potentially, could iterate again or add emergency portals.


    def generate_world(
        self, width: int, height: int, seed: int | None = None
    ) -> tuple[dict[int, WorldMap], tuple[int, int, int], tuple[int, int, int]]:
        """
        Generates a complete game world with multiple floors, portals,
        player start, and goal.

        Returns:
            A tuple containing:
                - world_maps (dict[int, WorldMap]): Dictionary of generated floors.
                - player_start_full_pos (tuple[int, int, int]): Player's start (x,y,floor_id).
                - actual_win_full_pos (tuple[int, int, int]): Goal item's (x,y,floor_id).
        """
        if seed is not None:
            random.seed(seed)

        num_floors = random.randint(2, 10)
        world_maps: dict[int, WorldMap] = {}

        floor_details = []

        for floor_id in range(num_floors):
            # Gen unique seed per floor for reproducibility if global seed is given.
            floor_seed = random.randint(0, 2**32 - 1) if seed else None

            world_map, floor_start_pos, floor_poi_pos = self._generate_single_floor(
                width, height, current_seed=floor_seed
            )
            world_maps[floor_id] = world_map
            floor_details.append({
                "id": floor_id, "map": world_map,
                "start": floor_start_pos, "poi": floor_poi_pos
            })

        self._ensure_portal_connectivity(world_maps, width, height)

        player_start_floor_id = 0
        player_start_x = floor_details[player_start_floor_id]["start"][0]
        player_start_y = floor_details[player_start_floor_id]["start"][1]
        player_start_full_pos = (player_start_x, player_start_y, player_start_floor_id)

        # Place Amulet on a different floor from player start.
        amulet_floor_id = player_start_floor_id
        if num_floors > 1:
            possible_floors = [f["id"] for f in floor_details
                               if f["id"] != player_start_floor_id]
            amulet_floor_id = (random.choice(possible_floors) if possible_floors
                               else (player_start_floor_id + 1) % num_floors)

        amulet_map = world_maps[amulet_floor_id]
        amulet_floor_tiles = self._collect_floor_tiles(amulet_map, width, height)

        # Temp: use single-floor furthest point. Start search from portal or POI.
        start_node_amulet = floor_details[amulet_floor_id]["poi"]
        amulet_portals = [
            (x, y) for x in range(1, width-1) for y in range(1, height-1)
            if amulet_map.get_tile(x,y) and amulet_map.get_tile(x,y).is_portal
        ]
        if amulet_portals:
            start_node_amulet = random.choice(amulet_portals)
        elif not amulet_floor_tiles:
            amulet_map.set_tile_type(1,1,"floor") # Error case
            amulet_floor_tiles.append((1,1))
            start_node_amulet = (1,1)

        actual_win_full_pos : tuple[int,int,int]
        if not amulet_floor_tiles:
            # Major fallback: Amulet on player start floor.
            amulet_x = world_maps[player_start_floor_id].width // 2
            amulet_y = world_maps[player_start_floor_id].height // 2
            world_maps[player_start_floor_id].set_tile_type(amulet_x, amulet_y, "floor")
            actual_win_full_pos = (amulet_x, amulet_y, player_start_floor_id)
        else:
            start_tile = amulet_map.get_tile(start_node_amulet[0], start_node_amulet[1])
            # If POI/portal became wall or invalid, pick any floor tile.
            if not start_tile or start_tile.type != "floor":
                 start_node_amulet = random.choice(amulet_floor_tiles)

            amulet_x, amulet_y = self.path_finder.find_furthest_point(
                amulet_map, start_node_amulet, width, height
            )
            actual_win_full_pos = (amulet_x, amulet_y, amulet_floor_id)

        # Place Amulet item.
        amulet_item = Item("Amulet of Yendor", "Object of quest!", {"type": "quest"})
        target_map = world_maps[actual_win_full_pos[2]]
        win_x, win_y, _ = actual_win_full_pos

        win_tile = target_map.get_tile(win_x, win_y)
        if not win_tile or win_tile.type != "floor": # Ensure win pos is floor
            target_map.set_tile_type(win_x, win_y, "floor")
            win_tile = target_map.get_tile(win_x, win_y)

        if win_tile and win_tile.item is not None: # Clear if item already there
            target_map.remove_item(win_x, win_y)

        target_map.place_item(amulet_item, win_x, win_y)

        # Populate floors with additional entities.
        for f_id, f_map in world_maps.items():
            all_f_tiles = self._collect_floor_tiles(f_map, width, height)

            f_player_start = player_start_full_pos[:2] if f_id == player_start_full_pos[2] else None
            f_amulet_pos = actual_win_full_pos[:2] if f_id == actual_win_full_pos[2] else None

            # Use floor's specific start/poi if global player/amulet not on this floor.
            ref_start = f_player_start or floor_details[f_id]["start"]
            ref_win = f_amulet_pos or floor_details[f_id]["poi"]

            self._place_additional_entities(
                f_map, all_f_tiles, ref_start, ref_win, width, height
            )

        return world_maps, player_start_full_pos, actual_win_full_pos

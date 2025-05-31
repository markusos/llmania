import random
from typing import Optional

from src.item import Item
from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.density import FloorDensityAdjuster
from src.map_algorithms.pathfinding import PathFinder
from src.monster import Monster
from src.world_map import WorldMap


class WorldGenerator:
    """
    Generates the game world, including the map layout, player starting position,
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
        max_steps: int = 200,
    ):
        """
        Performs a directed random walk from start_pos towards end_pos.
        """
        current_x, current_y = start_pos
        world_map.set_tile_type(current_x, current_y, "floor")  # Carve start_pos

        for _ in range(max_steps):
            if (current_x, current_y) == end_pos:
                break

            dx = end_pos[0] - current_x
            dy = end_pos[1] - current_y

            possible_directions = []
            # North
            if current_y > 1:
                possible_directions.append((0, -1, "N"))
            # South
            if current_y < map_height - 2:
                possible_directions.append((0, 1, "S"))
            # West
            if current_x > 1:
                possible_directions.append((-1, 0, "W"))
            # East
            if current_x < map_width - 2:
                possible_directions.append((1, 0, "E"))

            if not possible_directions:  # Should not happen in a >3x3 inner map
                break

            preferred_directions = []
            if dy < 0:  # North
                preferred_directions.append((0, -1, "N"))
            if dy > 0:  # South
                preferred_directions.append((0, 1, "S"))
            if dx < 0:  # West
                preferred_directions.append((-1, 0, "W"))
            if dx > 0:  # East
                preferred_directions.append((1, 0, "E"))

            # Filter preferred_directions to only those that are possible
            possible_moves_set = {(d[0], d[1], d[2]) for d in possible_directions}
            preferred_directions = [
                pd
                for pd in preferred_directions
                if (pd[0], pd[1], pd[2]) in possible_moves_set
            ]

            chosen_dx, chosen_dy = 0, 0
            # 75% chance to pick a preferred direction
            if preferred_directions and random.random() < 0.75:
                chosen_dx, chosen_dy, _ = random.choice(preferred_directions)
            else:  # Pick any allowed direction
                chosen_dx, chosen_dy, _ = random.choice(possible_directions)

            next_x, next_y = current_x + chosen_dx, current_y + chosen_dy

            # Check if next_pos is within inner map bounds (1 to width-2, 1 to height-2)
            if 1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1:
                tile = world_map.get_tile(next_x, next_y)
                if tile and (tile.type == "wall" or tile.type == "potential_floor"):
                    world_map.set_tile_type(next_x, next_y, "floor")
                current_x, current_y = next_x, next_y
            # If next_pos is not valid (hits border or invalid move),
            # walker stays, try new direction next step.
            # No explicit else needed, current_pos just doesn't update.

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
        num_quadrant_paths = 4  # Or make this a class/instance variable

        for quadrant_index in range(num_quadrant_paths):
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

    def generate_map(
        self, width: int, height: int, seed: int | None = None
    ) -> tuple[WorldMap, tuple[int, int], tuple[int, int]]:
        """
        Generates a complete game map with player start, goal, paths, items,
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
            seed: Optional seed for RNG for deterministic map generation.

        Returns:
            A tuple containing:
                - world_map (WorldMap): The generated game map.
                - player_start_pos (tuple[int, int]): Player's start (x,y) coordinates.
                - actual_win_pos (tuple[int, int]): Goal item's (x,y) coordinates.
        Raises:
            ValueError: If dimensions are less than 3x4 or 4x3, propagated from
                        _select_start_and_win_positions.
        """
        if (width < 3 or height < 4) and (width < 4 or height < 3):
            raise ValueError(
                "Map dimensions must be at least 3x4 or 4x3 for this generator."
            )

        world_map = self._initialize_map(width, height, seed)
        player_start_pos, original_win_pos = self._select_start_and_win_positions(
            width, height, world_map
        )

        self.path_finder.carve_bresenham_line(
            world_map, player_start_pos, original_win_pos, width, height
        )
        self._perform_random_walks(world_map, player_start_pos, width, height)

        # Convert remaining "potential_floor" tiles to "wall"
        for y_coord in range(1, height - 1):
            for x_coord in range(1, width - 1):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "potential_floor":
                    world_map.set_tile_type(x_coord, y_coord, "wall")

        # Adjust floor density
        self.density_adjuster.adjust_density(
            world_map,
            player_start_pos,
            original_win_pos,
            width,
            height,
            self.floor_portion,
        )

        # Ensure connectivity of all floor tiles
        self.connectivity_manager.ensure_connectivity(
            world_map, player_start_pos, width, height
        )

        # Collect final floor tiles for item/monster placement
        # _collect_floor_tiles remains in WorldGenerator for this purpose.
        floor_tiles = self._collect_floor_tiles(world_map, width, height)

        # Safeguard: Ensure player_start_pos and original_win_pos are floor tiles.
        # Should be guaranteed by _select_start_and_win_positions and _carve_path.
        # Empty floor_tiles indicates a critical failure in prior steps.
        if not floor_tiles:
            # This is a fallback for an unexpected state.
            # Ensure player_start_pos is floor and add it to floor_tiles.
            world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
            if player_start_pos not in floor_tiles:
                floor_tiles.append(player_start_pos)

            # Ensure original_win_pos is floor if different and map not 1x1.
            if original_win_pos != player_start_pos or (width == 1 and height == 1):
                world_map.set_tile_type(
                    original_win_pos[0], original_win_pos[1], "floor"
                )
                if original_win_pos not in floor_tiles:
                    floor_tiles.append(original_win_pos)

        # Place the goal item at the furthest reachable point.
        actual_win_pos = self._place_win_item_at_furthest_point(
            world_map, player_start_pos, width, height, floor_tiles
        )
        # Place other items and monsters.
        self._place_additional_entities(
            world_map, floor_tiles, player_start_pos, actual_win_pos, width, height
        )

        return world_map, player_start_pos, actual_win_pos

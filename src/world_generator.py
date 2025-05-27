import random
from typing import Optional
from collections import deque # Still needed for _perform_random_walks

from src.item import Item
from src.monster import Monster
from src.world_map import WorldMap
from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.density import FloorDensityAdjuster
from src.map_algorithms.pathfinding import PathFinder


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
        self.floor_portion = floor_portion if floor_portion is not None else self.DEFAULT_FLOOR_PORTION
        self.connectivity_manager = MapConnectivityManager()
        self.density_adjuster = FloorDensityAdjuster(self.connectivity_manager)
        self.path_finder = PathFinder()

    def _initialize_map(self, width: int, height: int, seed: Optional[int]) -> WorldMap:
        """
        Initializes a new WorldMap. The outermost layer is set to "wall",
        and inner tiles are set to "potential_floor".
        If a seed is provided, it initializes the random number generator.

        Args:
            width: The width of the map.
            height: The height of the map.
            seed: An optional seed for the random number generator.

        Returns:
            A WorldMap instance.
        """
        if seed is not None:
            random.seed(
                seed
            )  # Initialize RNG for deterministic generation if seed is given

        world_map = WorldMap(width, height)
        # Set tiles based on position: outer layer wall, inner potential_floor
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
            ValueError: If dimensions are less than 3x4 or 4x3, as valid "potential_floor"
                        tiles for start/win positions would not exist.
        """
        if (width < 3 or height < 4) and (width < 4 or height < 3):
            raise ValueError(
                "Map dimensions must be at least 3x4 or 4x3 to select start/win positions "
                "from 'potential_floor' tiles."
            )

        # Select player start and win positions from the inner "potential_floor" area
        # For 3x4: inner width=1, inner height=2. random.randint(1,1) and random.randint(1,2) are valid.
        # For 4x3: inner width=2, inner height=1. random.randint(1,2) and random.randint(1,1) are valid.
        player_start_x = random.randint(1, width - 2)
        player_start_y = random.randint(1, height - 2)
        win_x = random.randint(1, width - 2)
        win_y = random.randint(1, height - 2)

        player_start_pos = (player_start_x, player_start_y)
        original_win_pos = (win_x, win_y)

        # Ensure win_pos is different from player_start_pos.
        # Given width/height >= 3, map is at least 3x3, so player_start_pos != original_win_pos is possible.
        attempts = 0
        # Max attempts: roughly half the number of potential_floor cells as a heuristic
        max_attempts = ((width - 2) * (height - 2)) // 2 + 1
        if max_attempts <= 0 : max_attempts = 1 # Ensure at least one attempt if area is tiny (e.g. 3x3)


        while original_win_pos == player_start_pos:
            if attempts >= max_attempts:
                # This case should be rare in maps 3x3 or larger.
                # If all potential_floor cells are just one cell (3x3 map),
                # and player_start_pos is that cell, we need to allow it.
                # However, the loop condition `original_win_pos == player_start_pos`
                # implies we must find a different spot if possible.
                # If (width-2)*(height-2) is 1 (i.e. 3x3 map), this loop won't run if player_start_pos is the only option.
                # If it's >1, it should find a different pos.
                # For a 3x3 map, (width-2)*(height-2) = 1. max_attempts = 1.
                # If player_start_pos is (1,1), and original_win_pos is (1,1), loop runs.
                # win_x/win_y are re-rolled. They will still be 1. So original_win_pos remains (1,1).
                # This leads to an infinite loop if (width-2)*(height-2) == 1.
                if (width - 2) * (height - 2) == 1: # Single potential_floor cell
                    break # No other choice
                # Otherwise, it's a genuine failure to find a different spot, which is unexpected.
                # This could happen if random.randint consistently returns the same numbers.
                # For simplicity, we'll break and allow player_start_pos == original_win_pos
                # if max_attempts are exhausted on larger maps.
                # A more robust solution might involve iterating through all possible spots.
                break
            win_x = random.randint(1, width - 2)
            win_y = random.randint(1, height - 2)
            original_win_pos = (win_x, win_y)
            attempts += 1

        # Set the selected positions to be floor tiles
        world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
        world_map.set_tile_type(original_win_pos[0], original_win_pos[1], "floor")
        return player_start_pos, original_win_pos

    # _ensure_all_tiles_accessible was moved to MapConnectivityManager.ensure_connectivity
    # _carve_path was moved to PathFinder.carve_bresenham_line

    def _perform_random_walks(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> None:
        """
        Performs several random walks to carve out additional floor space,
        making the map more cavern-like and less linear.

        Args:
            world_map: The WorldMap instance to modify.
            player_start_pos: Player's starting position (one of the walk origins).
            map_width: The width of the map.
            map_height: The height of the map.
        """
        num_walks = 5  # Number of distinct random walks to perform
        walk_length = (map_width * map_height) // 10  # Max length of each walk

        # Collect all current floor tiles to use as potential start points for walks
        current_floor_tiles = self._collect_floor_tiles(
            world_map, map_width, map_height
        )
        if not current_floor_tiles:  # Should not happen if path carving was done
            current_floor_tiles = [player_start_pos]  # Fallback

        walk_start_points = [player_start_pos]  # Always start one walk from player
        # Add more random start points for other walks, if enough floor tiles exist
        for _ in range(num_walks - 1):
            if current_floor_tiles:
                walk_start_points.append(random.choice(current_floor_tiles))
            else:  # Should not be reached if current_floor_tiles has player_start_pos.
                walk_start_points.append(player_start_pos)

        for walk_start_x, walk_start_y in walk_start_points:
            current_x, current_y = walk_start_x, walk_start_y
            for _ in range(walk_length):
                # Choose a random cardinal direction
                directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # N, S, W, E
                dx_walk, dy_walk = random.choice(directions)
                next_x, next_y = current_x + dx_walk, current_y + dy_walk

                # Check if the next step is within map bounds
                if 0 <= next_x < map_width and 0 <= next_y < map_height:
                    # If the tile at next_x, next_y is a wall, turn it into a floor
                    tile_to_change = world_map.get_tile(next_x, next_y)
                    if tile_to_change and tile_to_change.type == "wall":
                        world_map.set_tile_type(next_x, next_y, "floor")
                    # Move walker to new position (even if not a wall).
                    current_x, current_y = next_x, next_y
                # If out of bounds, walker stays and tries new direction next step.

    def _collect_floor_tiles( # This method remains in WorldGenerator
        self, world_map: WorldMap, map_width: int, map_height: int
    ) -> list[tuple[int, int]]:
        """
        Scans the inner area of the map and returns a list of coordinates for all "floor" tiles.

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
        floor_tiles: list[tuple[int, int]], # Used for fallback, primary logic uses BFS
    ) -> tuple[int, int]:
        """
        Places the goal item ("Amulet of Yendor") at the floor tile furthest
        reachable from player_start_pos.

        Args:
            world_map: The WorldMap instance.
            player_start_pos: The player's starting position.
            map_width: The width of the map.
            map_height: The height of the map.
            floor_tiles: A list of all inner floor tile coordinates, for fallback.

        Returns:
            The (x,y) tuple of the actual position where the goal item was placed.
        """
        goal_item = Item(
            "Amulet of Yendor", "The object of your quest!", {"type": "quest"}
        )

        if not floor_tiles: 
            actual_win_pos = player_start_pos 
            if world_map.get_tile(player_start_pos[0], player_start_pos[1]).type != "floor":
                 world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
        else:
            # Find the furthest tile using PathFinder instance
            actual_win_pos = self.path_finder.find_furthest_point(
                world_map, player_start_pos, map_width, map_height
            )
            chosen_tile = world_map.get_tile(actual_win_pos[0], actual_win_pos[1])
            if not chosen_tile or chosen_tile.type != "floor":
                available_floor_for_goal = [
                    tile for tile in floor_tiles if tile != player_start_pos
                ]
                if not available_floor_for_goal and player_start_pos in floor_tiles:
                     actual_win_pos = player_start_pos
                elif available_floor_for_goal:
                     actual_win_pos = random.choice(available_floor_for_goal)
                else: # Ultimate fallback if floor_tiles was empty or player_start_pos not in it.
                     actual_win_pos = player_start_pos
                     if world_map.get_tile(player_start_pos[0], player_start_pos[1]).type != "floor":
                         world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")


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
            raise ValueError("Map dimensions must be at least 3x4 or 4x3 for this generator.")

        world_map = self._initialize_map(width, height, seed)
        player_start_pos, original_win_pos = self._select_start_and_win_positions(
            width, height, world_map # This will raise ValueError if width/height < 3
        )

        # Carve path using PathFinder
        self.path_finder.carve_bresenham_line(
            world_map, player_start_pos, original_win_pos, width, height
        )
        # Ensure connectivity using MapConnectivityManager
        self.connectivity_manager.ensure_connectivity( # Use the instance here
            world_map, player_start_pos, width, height
        )
        self._perform_random_walks(world_map, player_start_pos, width, height) # Remains internal
        
        # Adjust floor density using FloorDensityAdjuster
        self.density_adjuster.adjust_density( # Use the instance here
            world_map, player_start_pos, original_win_pos, width, height, self.floor_portion
        )

        # Collect final floor tiles for item placement.
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

import random
from typing import Optional

from src.item import Item
from src.monster import Monster
from src.world_map import WorldMap


class WorldGenerator:
    """
    Generates the game world, including the map layout, player starting position,
    the goal item's location, and placement of other items and monsters.
    """

    def _initialize_map(
        self, width: int, height: int, seed: Optional[int]
    ) -> WorldMap:
        """
        Initializes a new WorldMap of the given dimensions, filled entirely with walls.
        If a seed is provided, it initializes the random number generator.

        Args:
            width: The width of the map.
            height: The height of the map.
            seed: An optional seed for the random number generator.

        Returns:
            A WorldMap instance.
        """
        if seed is not None:
            random.seed(seed) # Initialize RNG for deterministic generation if seed is given

        world_map = WorldMap(width, height)
        # Fill the entire map with wall tiles initially
        for y in range(height):
            for x in range(width):
                world_map.set_tile_type(x, y, "wall")
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
        """
        # Select player start X, avoiding edges if map is wide enough
        if width < 3: # For maps 1 or 2 cells wide
            player_start_x = 0 if width == 1 else random.randint(0, width - 1)
            win_x = 0 if width == 1 else random.randint(0, width - 1)
        else: # For maps 3+ cells wide, keep away from edge
            player_start_x = random.randint(1, width - 2)
            win_x = random.randint(1, width - 2)

        # Select player start Y, avoiding edges if map is tall enough
        if height < 3:
            player_start_y = 0 if height == 1 else random.randint(0, height - 1)
            win_y = 0 if height == 1 else random.randint(0, height - 1)
        else:
            player_start_y = random.randint(1, height - 2)
            win_y = random.randint(1, height - 2)

        player_start_pos = (player_start_x, player_start_y)
        original_win_pos = (win_x, win_y)

        # Ensure win_pos is different from player_start_pos, unless map is 1x1.
        if not (width == 1 and height == 1):
            attempts = 0
            max_attempts = (width * height) * 2 # Heuristic to prevent infinite loops
            while original_win_pos == player_start_pos:
                if attempts >= max_attempts:
                    # If too many attempts, it's possible all valid spots are the same as player_start_pos
                    # (e.g. on a 1x2 map, if player starts at (0,0), win_pos must be (0,1) or vice-versa).
                    # This loop primarily handles larger maps where random chance might pick same spot.
                    break 
                # Reselect win_pos coordinates using the same edge-avoidance logic
                win_x = random.randint(1, width - 2) if width >=3 else (0 if width == 1 else random.randint(0, width-1))
                win_y = random.randint(1, height - 2) if height >=3 else (0 if height == 1 else random.randint(0, height-1))
                original_win_pos = (win_x, win_y)
                attempts += 1
        
        # Set the selected positions to be floor tiles
        world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
        world_map.set_tile_type(original_win_pos[0], original_win_pos[1], "floor")
        return player_start_pos, original_win_pos

    def _carve_path(
        self,
        world_map: WorldMap,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> None:
        """
        Carves a path of "floor" tiles between start_pos and end_pos using a
        Bresenham-like line algorithm. Ensures the path stays within map bounds.

        Args:
            world_map: The WorldMap instance to modify.
            start_pos: The (x,y) starting coordinates of the path.
            end_pos: The (x,y) ending coordinates of the path.
            map_width: The total width of the map for bounds checking.
            map_height: The total height of the map for bounds checking.
        """
        path_points = []
        curr_x, curr_y = start_pos
        dx = end_pos[0] - curr_x
        dy = end_pos[1] - curr_y
        steps = max(abs(dx), abs(dy)) # Number of steps needed for the longer axis

        if steps == 0: # Start and end are the same point
            if 0 <= curr_x < map_width and 0 <= curr_y < map_height:
                 path_points.append(start_pos)
        else:
            x_increment = dx / steps
            y_increment = dy / steps
            # Iterate for each step, calculating and rounding coordinates
            for i in range(steps + 1): # Include the end point
                px = round(curr_x + i * x_increment)
                py = round(curr_y + i * y_increment)
                # Ensure path points are within map bounds before adding to path list
                if 0 <= px < map_width and 0 <= py < map_height:
                    path_points.append((px, py))
        
        # Set all unique points in the path to "floor"
        for px, py in set(path_points): # Use set to avoid redundant calls for same tile
            # Double check bounds, though round() might take it out.
            if 0 <= px < map_width and 0 <= py < map_height:
                world_map.set_tile_type(px, py, "floor")

    def _perform_random_walks(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> None:
        """
        Performs several random walks across the map to carve out additional floor space,
        making the map more cavern-like and less linear.

        Args:
            world_map: The WorldMap instance to modify.
            player_start_pos: The player's starting position, used as one of the walk origins.
            map_width: The width of the map.
            map_height: The height of the map.
        """
        num_walks = 5  # Number of distinct random walks to perform
        walk_length = (map_width * map_height) // 10  # Max length of each walk

        # Collect all current floor tiles to use as potential start points for walks
        current_floor_tiles = self._collect_floor_tiles(world_map, map_width, map_height)
        if not current_floor_tiles: # Should not happen if path carving was done
            current_floor_tiles = [player_start_pos] # Fallback

        walk_start_points = [player_start_pos] # Always start one walk from player
        # Add more random start points for other walks, if enough floor tiles exist
        for _ in range(num_walks - 1):
            if current_floor_tiles:
                walk_start_points.append(random.choice(current_floor_tiles))
            else: # Should not be reached if current_floor_tiles has at least player_start_pos
                walk_start_points.append(player_start_pos)


        for walk_start_x, walk_start_y in walk_start_points:
            current_x, current_y = walk_start_x, walk_start_y
            for _ in range(walk_length):
                # Choose a random cardinal direction
                directions = [(0, -1), (0, 1), (-1, 0), (1, 0)] # N, S, W, E
                dx_walk, dy_walk = random.choice(directions)
                next_x, next_y = current_x + dx_walk, current_y + dy_walk

                # Check if the next step is within map bounds
                if 0 <= next_x < map_width and 0 <= next_y < map_height:
                    # If the tile at next_x, next_y is a wall, turn it into a floor
                    tile_to_change = world_map.get_tile(next_x, next_y)
                    if tile_to_change and tile_to_change.type == "wall":
                        world_map.set_tile_type(next_x, next_y, "floor")
                    # Move the walker to the new position (even if it wasn't a wall)
                    current_x, current_y = next_x, next_y
                # If out of bounds, walker effectively stays and tries a new direction next step

    def _collect_floor_tiles(
        self, world_map: WorldMap, map_width: int, map_height: int
    ) -> list[tuple[int, int]]:
        """
        Scans the entire map and returns a list of coordinates for all "floor" tiles.

        Args:
            world_map: The WorldMap to scan.
            map_width: The width of the map.
            map_height: The height of the map.

        Returns:
            A list of (x,y) tuples representing floor tile coordinates.
        """
        floor_tiles = []
        for y_coord in range(map_height):
            for x_coord in range(map_width):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "floor":
                    floor_tiles.append((x_coord, y_coord))
        return floor_tiles

    def _place_goal_item(
        self,
        world_map: WorldMap,
        original_win_pos: tuple[int, int],
        floor_tiles: list[tuple[int, int]],
        player_start_pos: tuple[int, int],
    ) -> tuple[int, int]:
        """
        Places the goal item ("Amulet of Yendor") on the map.
        Tries to place it at `original_win_pos`. If that's not a floor tile
        (which shouldn't happen if path carving worked), it uses a fallback.

        Args:
            world_map: The WorldMap instance.
            original_win_pos: The initially selected winning position.
            floor_tiles: A list of all floor tile coordinates.
            player_start_pos: The player's starting position, to avoid placing goal item there if possible.

        Returns:
            The (x,y) tuple of the actual position where the goal item was placed.
        """
        goal_item = Item(
            "Amulet of Yendor", "The object of your quest!", {"type": "quest"}
        )
        actual_win_pos = original_win_pos # Assume original is fine initially

        # Check if original_win_pos is a valid floor tile for placing the item.
        tile_at_original_win = world_map.get_tile(original_win_pos[0], original_win_pos[1])
        if tile_at_original_win and tile_at_original_win.type == "floor":
            world_map.place_item(goal_item, original_win_pos[0], original_win_pos[1])
        else:
            # Fallback: original_win_pos is not a floor tile (e.g., if random walks overwrote it, though unlikely).
            # Try to place on any other available floor tile, avoiding player_start_pos if possible.
            available_floor_for_goal = [tile for tile in floor_tiles if tile != player_start_pos]
            if not available_floor_for_goal and floor_tiles: # Only player_start_pos is floor
                 available_floor_for_goal = floor_tiles # Allow placing on player_start_pos if it's the only option
            
            if available_floor_for_goal:
                chosen_pos = random.choice(available_floor_for_goal)
                actual_win_pos = chosen_pos
                world_map.place_item(goal_item, actual_win_pos[0], actual_win_pos[1])
            else:
                # Ultimate fallback: player_start_pos (which should always be made floor).
                # This case means no floor tiles were found at all, which is highly problematic
                # but we ensure the item is placed somewhere.
                actual_win_pos = player_start_pos
                # Ensure player_start_pos is floor if it somehow wasn't
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
        Places a number of additional items (potions, daggers) and monsters (goblins, bats)
        randomly on available floor tiles. Avoids placing them on the player's start
        position or the actual winning position.

        Args:
            world_map: The WorldMap instance.
            floor_tiles: A list of all floor tile coordinates.
            player_start_pos: The player's starting position.
            actual_win_pos: The actual position of the goal item.
            map_width: The width of the map.
            map_height: The height of the map.
        """
        if not floor_tiles: # No floor tiles to place entities on.
            return

        # Determine number of entities to try placing based on map size.
        num_placements = (map_width * map_height) // 15 # Example density
        
        # Filter floor_tiles to get spots available for random entities.
        # Exclude player start and the goal item's location.
        available_floor_tiles_for_entities = [
            tile for tile in floor_tiles 
            if tile != player_start_pos and tile != actual_win_pos
        ]

        for _ in range(num_placements):
            if not available_floor_tiles_for_entities: # No more valid spots
                break

            # Choose a random available tile and remove it from list to ensure unique placement per attempt
            chosen_tile_index = random.randrange(len(available_floor_tiles_for_entities))
            chosen_tile_pos = available_floor_tiles_for_entities.pop(chosen_tile_index)
            
            # Check if the chosen tile object is indeed empty (it should be, as we picked from available floor)
            tile_obj = world_map.get_tile(chosen_tile_pos[0], chosen_tile_pos[1])
            if tile_obj and tile_obj.item is None and tile_obj.monster is None:
                # Decide whether to place an item or a monster
                if random.random() < 0.15:  # 15% chance to place an item
                    # Randomly choose between a health potion and a dagger
                    if random.random() < 0.5:
                        item_to_place = Item("Health Potion", "Restores some HP.", {"type": "heal", "amount": 10})
                    else:
                        item_to_place = Item("Dagger", "A small blade.", {"type": "weapon", "attack_bonus": 2, "verb": "stabs"})
                    world_map.place_item(item_to_place, chosen_tile_pos[0], chosen_tile_pos[1])
                elif random.random() < 0.10:  # 10% chance to place a monster (after failing item placement)
                    # Randomly choose between a goblin and a bat
                    if random.random() < 0.5:
                        monster_to_place = Monster("Goblin", 10, 3, x=chosen_tile_pos[0], y=chosen_tile_pos[1])
                    else:
                        monster_to_place = Monster("Bat", 5, 2, x=chosen_tile_pos[0], y=chosen_tile_pos[1])
                    world_map.place_monster(monster_to_place, chosen_tile_pos[0], chosen_tile_pos[1])

    def generate_map(
        self, width: int, height: int, seed: int | None = None
    ) -> tuple[WorldMap, tuple[int, int], tuple[int, int]]:
        """
        Generates a complete game map with a player start, goal, paths, items, and monsters.

        The process involves:
        1. Initializing a map full of walls.
        2. Selecting player start and initial win positions, making them floor.
        3. Carving a guaranteed path between player start and win positions.
        4. Performing random walks to create more open floor areas.
        5. Collecting all floor tiles.
        6. Placing the goal item (Amulet of Yendor), potentially adjusting win position.
        7. Placing additional items and monsters on available floor tiles.

        Args:
            width: The desired width of the map.
            height: The desired height of the map.
            seed: An optional seed for the random number generator for deterministic map generation.

        Returns:
            A tuple containing:
                - world_map (WorldMap): The generated game map.
                - player_start_pos (tuple[int, int]): The (x,y) coordinates of the player's start.
                - actual_win_pos (tuple[int, int]): The (x,y) coordinates of the goal item.
        """
        world_map = self._initialize_map(width, height, seed)
        player_start_pos, original_win_pos = self._select_start_and_win_positions(
            width, height, world_map
        )

        # Carve a path and perform random walks to make the map navigable and interesting.
        self._carve_path(world_map, player_start_pos, original_win_pos, width, height)
        self._perform_random_walks(world_map, player_start_pos, width, height)

        # After all floor carving, collect all tiles that are now floor.
        floor_tiles = self._collect_floor_tiles(world_map, width, height)

        # Safeguard: Ensure player_start_pos and original_win_pos are indeed floor tiles.
        # This should ideally be guaranteed by _select_start_and_win_positions and _carve_path.
        # If floor_tiles is empty, it indicates a critical failure in prior steps.
        if not floor_tiles:
            # This is a fallback for an unexpected state.
            # Ensure player_start_pos is floor and add it to floor_tiles.
            world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
            if player_start_pos not in floor_tiles: floor_tiles.append(player_start_pos)
            
            # Also ensure original_win_pos is floor if it's different and map is not 1x1.
            if original_win_pos != player_start_pos or (width==1 and height==1):
                 world_map.set_tile_type(original_win_pos[0], original_win_pos[1], "floor")
                 if original_win_pos not in floor_tiles: floor_tiles.append(original_win_pos)

        # Place the goal item and get its final position.
        actual_win_pos = self._place_goal_item(
            world_map, original_win_pos, floor_tiles, player_start_pos
        )
        # Place other items and monsters.
        self._place_additional_entities(
            world_map, floor_tiles, player_start_pos, actual_win_pos, width, height
        )

        return world_map, player_start_pos, actual_win_pos

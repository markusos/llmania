import random

from src.item import Item
from src.monster import Monster
from src.world_map import WorldMap


class WorldGenerator:
    def generate_map(
        self, width: int, height: int, seed: int | None = None
    ) -> tuple[WorldMap, tuple[int, int], tuple[int, int]]:
        # 1. Initialization
        if seed is not None:
            random.seed(seed)

        world_map = WorldMap(width, height)
        for y in range(height):
            for x in range(width):
                world_map.set_tile_type(x, y, "wall")

        # 2. Select Start and Win Positions
        # Ensure width/height are large enough for randint(1, dim-2)
        # If width/height is 1 or 2, randint will fail.
        # For simplicity, the problem states "avoid edges for now".
        # This implies width/height >= 3. If they are smaller, this logic needs
        # adjustment.
        # A robust solution would handle small maps, but following current problem spec.
        if width < 3:  # Ensure player_x can be selected
            player_start_x = 0 if width == 1 else random.randint(0, width - 1)
            win_x = 0 if width == 1 else random.randint(0, width - 1)
        else:
            player_start_x = random.randint(1, width - 2)
            win_x = random.randint(1, width - 2)

        if height < 3:  # Ensure player_y can be selected
            player_start_y = 0 if height == 1 else random.randint(0, height - 1)
            win_y = 0 if height == 1 else random.randint(0, height - 1)
        else:
            player_start_y = random.randint(1, height - 2)
            win_y = random.randint(1, height - 2)

        player_start_pos = (player_start_x, player_start_y)
        win_pos = (win_x, win_y)

        # Ensure win_pos is different from player_start_pos, unless map is too small for them to be different
        if not (width == 1 and height == 1): # Only try to find a new win_pos if map is larger than 1x1
            attempts = 0 # Add attempt counter to prevent potential infinite loops on slightly larger small maps
            max_attempts = (width * height) * 2 # Heuristic for max attempts

            while win_pos == player_start_pos:
                if attempts >= max_attempts:
                    # Could not find a different win_pos, break.
                    # This might happen on very small maps if random choices are unlucky.
                    # For 1x2, 2x1, 2x2, it should generally find one.
                    break 
                if width < 3:
                    win_x = 0 if width == 1 else random.randint(0, width - 1)
                else:
                    win_x = random.randint(1, width - 2)
                if height < 3:
                    win_y = 0 if height == 1 else random.randint(0, height - 1)
                else:
                    win_y = random.randint(1, height - 2)
                win_pos = (win_x, win_y)
                attempts += 1
        # For a 1x1 map, win_pos will remain == player_start_pos, which is correct.

        world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
        world_map.set_tile_type(win_pos[0], win_pos[1], "floor")

        # 3. Carve Guaranteed Path (Bresenham-like line)
        path = []
        curr_x, curr_y = player_start_pos
        dx = win_pos[0] - curr_x
        dy = win_pos[1] - curr_y
        steps = max(abs(dx), abs(dy))

        if steps == 0:
            path.append(player_start_pos)
        else:
            x_increment = dx / steps
            y_increment = dy / steps
            for i in range(steps + 1):  # Include the end point
                px = round(curr_x + i * x_increment)
                py = round(curr_y + i * y_increment)
                # Ensure path points are within bounds before adding to path list
                if 0 <= px < width and 0 <= py < height:
                    path.append((px, py))

        for px, py in path:
            # Double check bounds, though round() might take it out.
            if 0 <= px < width and 0 <= py < height:
                world_map.set_tile_type(px, py, "floor")

        # 4. Additional Random Walks for Exploration
        num_walks = 5  # Number of random walks
        walk_length = (width * height) // 10  # Length of each walk

        all_floor_tiles_for_walk_starts = [
            player_start_pos
        ]  # Start one walk from player

        # Get current floor tiles to potentially start other walks
        temp_floor_tiles = []
        for y_coord in range(height):
            for x_coord in range(width):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "floor":
                    temp_floor_tiles.append((x_coord, y_coord))
        if not temp_floor_tiles:  # Should not happen due to path carving
            temp_floor_tiles.append(player_start_pos)

        for _ in range(num_walks - 1):  # Add more start points for walks
            all_floor_tiles_for_walk_starts.append(random.choice(temp_floor_tiles))

        for walk_start_x, walk_start_y in all_floor_tiles_for_walk_starts:
            current_x, current_y = walk_start_x, walk_start_y
            for _ in range(walk_length):
                directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
                dx_walk, dy_walk = random.choice(directions)
                next_x, next_y = current_x + dx_walk, current_y + dy_walk

                if 0 <= next_x < width and 0 <= next_y < height:
                    # Critical change: Only convert "wall" to "floor"
                    tile_to_change = world_map.get_tile(next_x, next_y)
                    if tile_to_change and tile_to_change.type == "wall":
                        world_map.set_tile_type(next_x, next_y, "floor")
                    current_x, current_y = (
                        next_x,
                        next_y,
                    )  # Walker moves regardless of tile type
                # If out of bounds, walker effectively stays and tries a new
                # direction next step

        # 5. Collect Floor Tiles, Place Goal Item, Other Items/Monsters
        floor_tiles = []
        for y_coord in range(height):
            for x_coord in range(width):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "floor":
                    floor_tiles.append((x_coord, y_coord))

        # If somehow no floor tiles (e.g. 1x1 map, path carving was just one point)
        # This should be very rare with the new logic.
        if not floor_tiles:
            # Fallback: ensure player_start_pos is floor if nothing else is
            world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
            floor_tiles.append(player_start_pos)
            # If win_pos was different and also got obliterated, make it same as
            # player_start_pos
            if win_pos not in floor_tiles:
                world_map.set_tile_type(
                    win_pos[0], win_pos[1], "floor"
                )  # Ensure it's floor
                if win_pos not in floor_tiles:
                    floor_tiles.append(win_pos)

        goal_item = Item(
            "Amulet of Yendor", "The object of your quest!", {"type": "quest"}
        )
        # Ensure win_pos is actually a floor tile before placing. Path carving
        # should ensure this.
        if world_map.get_tile(win_pos[0], win_pos[1]).type == "floor":
            world_map.place_item(goal_item, win_pos[0], win_pos[1])
        else:
            # Fallback if win_pos is not floor (should not happen with path carving)
            # Place it on player_start_pos or first available floor tile
            fallback_win_pos = player_start_pos
            if not floor_tiles:  # Extreme edge case, no floor tiles at all
                world_map.set_tile_type(
                    player_start_pos[0], player_start_pos[1], "floor"
                )
                floor_tiles.append(player_start_pos)

            if floor_tiles:
                fallback_win_pos = random.choice(floor_tiles)
                win_pos = (
                    fallback_win_pos  # Update win_pos to where item is actually placed
                )
                world_map.place_item(goal_item, win_pos[0], win_pos[1])

        num_placements = (width * height) // 15  # Adjusted placement attempts slightly
        for _ in range(num_placements):
            if not floor_tiles:
                break

            chosen_tile_pos = random.choice(floor_tiles)
            tile_obj = world_map.get_tile(chosen_tile_pos[0], chosen_tile_pos[1])

            # Only place if tile is empty and not player_start_pos or win_pos
            if (
                tile_obj
                and tile_obj.item is None
                and tile_obj.monster is None
                and chosen_tile_pos != player_start_pos
                and chosen_tile_pos != win_pos
            ):
                if random.random() < 0.15:  # Chance to place an item (e.g. 15%)
                    # Example: Potion or a simple weapon
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

                elif random.random() < 0.10:  # Chance to place a monster (e.g. 10%)
                    # Example: Goblin or Bat
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

        return world_map, player_start_pos, win_pos

import random
from typing import List, Optional, Tuple

from src.map_builders.world_builder import WorldBuilder
from src.world_map import WorldMap


class WorldGenerator:
    def __init__(self, floor_portion: Optional[float] = None):
        # floor_portion is now handled by SingleFloorBuilder,
        # but we keep it here if WorldGenerator needs to pass it down.
        self.floor_portion = floor_portion
        self.seed = None

    def generate_world(
        self, width: int, height: int, seed: Optional[int] = None
    ) -> Tuple[
        dict[int, WorldMap], Tuple[int, int, int], Tuple[int, int, int], List[dict]
    ]:
        self.seed = seed

        # Determine the number of floors for the world
        # This could be a fixed number, a range, or passed as a parameter
        num_floors = random.randint(2, 5)  # Example: 2 to 5 floors

        world_builder = WorldBuilder(width, height, seed=seed, num_floors=num_floors)
        # The WorldBuilder's build method now handles the entire world generation
        world_maps, player_start_full_pos, amulet_full_pos, floor_details = (
            world_builder.build()
        )

        return world_maps, player_start_full_pos, amulet_full_pos, floor_details

    # Methods like _generate_single_floor, _ensure_portal_connectivity, etc.,
    # are now part of SingleFloorBuilder or WorldBuilder.
    # Utility methods like _get_quadrant_bounds, _get_random_tile_in_bounds, etc.,
    # if still needed by WorldGenerator for other purposes (unlikely now),
    # would remain or be moved to a common utility module.
    # For now, we assume they are fully encapsulated within the builders.

    # The _print_debug_map can be kept if direct debugging from WorldGenerator
    # is needed, or moved to a utility if it's generally useful.
    def _print_debug_map(
        self,
        world_map: WorldMap,
        width: int,
        height: int,
        highlight_coords: Optional[List[Tuple[int, int]]] = None,
    ) -> None:
        print(f"--- Debug Map {width}x{height} ---")
        highlights = highlight_coords or []
        for y_coord in range(height):
            row_str = ""
            for x_coord in range(width):
                char = "?"
                if tile := world_map.get_tile(x_coord, y_coord):
                    if (x_coord, y_coord) in highlights:
                        char = "*"
                    elif tile.is_portal:
                        char = "P"
                    elif tile.type == "wall":
                        char = "#"
                    elif tile.type == "floor":
                        char = "."
                    elif (
                        tile.type == "potential_floor"
                    ):  # Should ideally not be present
                        char = "~"
                row_str += char + " "
            print(row_str)
        print("----------------------")

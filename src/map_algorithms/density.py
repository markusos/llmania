from typing import TYPE_CHECKING, List, Optional, Set, Tuple

from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.pathfinding import PathFinder
from src.world_map import WorldMap

if TYPE_CHECKING:
    from random import Random


class FloorDensityAdjuster:
    def __init__(
        self,
        connectivity_manager: MapConnectivityManager,
        random_generator: "Random",
    ):
        self.connectivity_manager = connectivity_manager
        self.random = random_generator

    def adjust_density(
        self,
        world_map: WorldMap,
        player_start_pos: Tuple[int, int],
        original_win_pos: Tuple[int, int],
        width: int,
        height: int,
        target_floor_portion: float,
        protected_coords: Optional[List[Tuple[int, int]]] = None,
    ) -> None:
        if not (0 < target_floor_portion < 1):
            return

        effective_protected_coords: Set[Tuple[int, int]] = set(protected_coords or [])
        effective_protected_coords.add(player_start_pos)
        effective_protected_coords.add(original_win_pos)

        # Explicitly protect the path between player_start_pos and original_win_pos
        # This is a direct way to ensure this path is not broken by density adjustments.
        # This might make the density adjustment less "natural" if this path is long
        # and the target density is very low, but it ensures critical connectivity.
        path_finder = PathFinder()  # PathFinder should be available or passed
        critical_path = path_finder.a_star_search(
            world_map, player_start_pos, original_win_pos, width, height
        )
        if critical_path:
            for path_node in critical_path:
                effective_protected_coords.add(path_node)

        total_placeable_tiles = (width - 2) * (height - 2)
        if total_placeable_tiles <= 0:
            return

        target_floor_tiles = int(total_placeable_tiles * target_floor_portion)

        current_floor_tiles: List[Tuple[int, int]] = []
        for r_y in range(1, height - 1):
            for r_x in range(1, width - 1):
                coord = (r_x, r_y)
                tile = world_map.get_tile(r_x, r_y)
                if tile and tile.type == "floor":
                    current_floor_tiles.append(coord)

        num_current_floor = len(current_floor_tiles)

        def is_adjacent_to_floor_tile(x: int, y: int, current_map: WorldMap) -> bool:
            for dx_offset, dy_offset in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                adj_x, adj_y = x + dx_offset, y + dy_offset
                if not (0 <= adj_x < width and 0 <= adj_y < height):
                    continue
                adj_tile = current_map.get_tile(adj_x, adj_y)
                if adj_tile and adj_tile.type == "floor":
                    return True
            return False

        candidate_walls_to_floor: List[Tuple[int, int]] = []
        if num_current_floor < target_floor_tiles:
            for r_y in range(1, height - 1):
                for r_x in range(1, width - 1):
                    coord = (r_x, r_y)
                    if coord in effective_protected_coords:
                        continue
                    tile = world_map.get_tile(r_x, r_y)
                    if tile and tile.type == "wall":
                        is_adjacent_to_floor = is_adjacent_to_floor_tile(
                            r_x, r_y, world_map
                        )
                        if is_adjacent_to_floor:
                            # Store without adjacent_floor_count for now,
                            # can be added if needed for sorting.
                            candidate_walls_to_floor.append((r_x, r_y))

        if num_current_floor < target_floor_tiles:
            while num_current_floor < target_floor_tiles:
                walls_to_add = []
                for r_y in range(1, height - 1):
                    for r_x in range(1, width - 1):
                        coord = (r_x, r_y)
                        if coord in effective_protected_coords:
                            continue
                        tile = world_map.get_tile(r_x, r_y)
                        if tile and tile.type == "wall":
                            if is_adjacent_to_floor_tile(r_x, r_y, world_map):
                                walls_to_add.append(coord)

                if not walls_to_add:
                    break  # No more walls can be converted

                self.random.shuffle(walls_to_add)

                converted_in_pass = 0
                for c_x, c_y in walls_to_add:
                    if num_current_floor >= target_floor_tiles:
                        break
                    world_map.set_tile_type(c_x, c_y, "floor")
                    num_current_floor += 1
                    converted_in_pass += 1

                if converted_in_pass == 0:
                    break  # No progress made
        if num_current_floor > target_floor_tiles:
            # effective_protected_coords already includes player_start_pos
            # and original_win_pos.
            candidate_floors_to_wall = [
                (f_x, f_y)
                for f_x in range(1, width - 1)
                for f_y in range(1, height - 1)
                if (f_x, f_y) not in effective_protected_coords
                and world_map.get_tile(f_x, f_y)
                and world_map.get_tile(f_x, f_y).type == "floor"
            ]
            self.random.shuffle(candidate_floors_to_wall)

            tiles_to_convert = num_current_floor - target_floor_tiles
            converted_count = 0
            for c_x, c_y in candidate_floors_to_wall:
                if converted_count >= tiles_to_convert:
                    break

                # Articulation point heuristic
                original_type = world_map.get_tile(c_x, c_y).type
                world_map.set_tile_type(c_x, c_y, "wall")

                if not self.connectivity_manager.path_exists_between(
                    world_map, player_start_pos, original_win_pos, width, height
                ):
                    world_map.set_tile_type(c_x, c_y, original_type)  # type: ignore
                    continue

                all_portals_still_reachable = True
                portals_on_this_floor = [
                    pc
                    for pc in effective_protected_coords
                    if pc != player_start_pos
                    and pc != original_win_pos
                    and (tile := world_map.get_tile(pc[0], pc[1]))
                    and tile.is_portal
                ]
                if portals_on_this_floor:
                    for portal_coord in portals_on_this_floor:
                        if not self.connectivity_manager.path_exists_between(
                            world_map, player_start_pos, portal_coord, width, height
                        ):
                            all_portals_still_reachable = False
                            break

                if all_portals_still_reachable:
                    converted_count += 1
                else:
                    world_map.set_tile_type(c_x, c_y, original_type)  # type: ignore

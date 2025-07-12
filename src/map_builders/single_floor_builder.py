import random
from typing import List, Optional, Tuple

from src.item import Item
from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.density import FloorDensityAdjuster
from src.map_algorithms.pathfinding import PathFinder
from src.map_builders.builder_base import BuilderBase
from src.monster import Monster
from src.world_map import WorldMap


class SingleFloorBuilder(BuilderBase):
    DEFAULT_FLOOR_PORTION = 0.5

    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
        floor_portion: Optional[float] = None,
        existing_map: Optional[WorldMap] = None,
    ):
        super().__init__(width, height, seed)
        if seed is not None:
            random.seed(seed)

        self.floor_portion = (
            floor_portion if floor_portion is not None else self.DEFAULT_FLOOR_PORTION
        )
        self.connectivity_manager = MapConnectivityManager()
        self.density_adjuster = FloorDensityAdjuster(self.connectivity_manager)
        self.path_finder = PathFinder()
        self.world_map = (
            existing_map if existing_map else self._initialize_map(width, height)
        )
        self.portals_on_floor: List[Tuple[int, int]] = []
        self.portal_destinations: dict[Tuple[int, int], Optional[int]] = {}

    def _initialize_map(self, width: int, height: int) -> WorldMap:
        world_map = WorldMap(width, height)
        for y_coord in range(height):
            for x_coord in range(width):
                if (
                    x_coord == 0
                    or x_coord == width - 1
                    or y_coord == 0
                    or y_coord == height - 1
                ):
                    world_map.set_tile_type(x_coord, y_coord, "wall")
                else:
                    world_map.set_tile_type(x_coord, y_coord, "potential_floor")
        return world_map

    def _get_quadrant_bounds(
        self, quadrant_index: int, map_width: int, map_height: int
    ) -> tuple[int, int, int, int]:
        mid_x = map_width // 2
        mid_y = map_height // 2
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
        min_x = max(inner_min_x, min_x)
        min_y = max(inner_min_y, min_y)
        max_x = min(inner_max_x, max_x)
        max_y = min(inner_max_y, max_y)
        if min_x > max_x:
            max_x = min_x
        if min_y > max_y:
            max_y = min_y
        return min_x, min_y, max_x, max_y

    def _get_random_tile_in_bounds(
        self,
        bounds: tuple[int, int, int, int],
        tile_type: str,
        max_attempts: int = 100,
    ) -> Optional[tuple[int, int]]:
        min_x, min_y, max_x, max_y = bounds
        if min_x > max_x or min_y > max_y:
            return None
        for _ in range(max_attempts):
            if max_x < min_x or max_y < min_y:  # type: ignore
                return None
            rand_x, rand_y = random.randint(min_x, max_x), random.randint(min_y, max_y)
            if (
                tile := self.world_map.get_tile(rand_x, rand_y)
            ) and tile.type == tile_type:
                return rand_x, rand_y
        return None

    def _perform_directed_random_walk(
        self,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
    ):
        current_x, current_y = start_pos
        if (current_x, current_y) not in self.portals_on_floor:
            self.world_map.set_tile_type(current_x, current_y, "floor")

        last_dx, last_dy = 0, 0
        current_walk_max_steps = 75
        if self.floor_portion < 0.35:
            current_walk_max_steps = 40
        path_history = [(current_x, current_y)]
        stuck_count = 0
        max_stuck_attempts = 5

        for _ in range(current_walk_max_steps):
            if (current_x, current_y) == end_pos:
                break
            dx_target, dy_target = end_pos[0] - current_x, end_pos[1] - current_y
            possible_directions = []
            for d_dx, d_dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                if (
                    1 <= current_x + d_dx < self.width - 1
                    and 1 <= current_y + d_dy < self.height - 1
                ):
                    possible_directions.append((d_dx, d_dy))
            if not possible_directions:
                break

            preferred_directions = []
            if dy_target < 0 and (0, -1) in possible_directions:
                preferred_directions.append((0, -1))
            if dy_target > 0 and (0, 1) in possible_directions:
                preferred_directions.append((0, 1))
            if dx_target < 0 and (-1, 0) in possible_directions:
                preferred_directions.append((-1, 0))
            if dx_target > 0 and (1, 0) in possible_directions:
                preferred_directions.append((1, 0))

            chosen_dx, chosen_dy = (
                random.choice(possible_directions) if possible_directions else (0, 0)
            )
            if preferred_directions and random.random() < 0.75:
                chosen_dx, chosen_dy = random.choice(preferred_directions)

            if (
                (last_dx, last_dy) != (0, 0)
                and (last_dx, last_dy) in possible_directions
                and random.random() < 0.6
            ):
                chosen_dx, chosen_dy = last_dx, last_dy

            if chosen_dx == 0 and chosen_dy == 0 and not possible_directions:
                break

            next_x, next_y = current_x + chosen_dx, current_y + chosen_dy
            last_dx, last_dy = chosen_dx, chosen_dy

            if (next_x, next_y) not in self.portals_on_floor:
                if (tile := self.world_map.get_tile(next_x, next_y)) and (
                    tile.type == "wall" or tile.type == "potential_floor"
                ):
                    self.world_map.set_tile_type(next_x, next_y, "floor")

            current_x, current_y = next_x, next_y
            path_history.append((current_x, current_y))

            if len(path_history) > 1 and (current_x, current_y) != path_history[-2]:
                stuck_count = 0
            else:
                stuck_count += 1
            if stuck_count >= max_stuck_attempts and len(path_history) > 1:
                for _ in range(min(3, len(path_history) - 1)):
                    if len(path_history) > 1:
                        path_history.pop()
                if path_history:
                    current_x, current_y = path_history[-1]
                stuck_count = 0

    def _perform_random_walks_respecting_portals(
        self,
        player_start_pos: tuple[int, int],
    ):
        for quadrant_index in range(4):
            quadrant_bounds = self._get_quadrant_bounds(
                quadrant_index, self.width, self.height
            )
            if (
                quadrant_bounds[0] > quadrant_bounds[2]
                or quadrant_bounds[1] > quadrant_bounds[3]
            ):
                continue

            start_node = self._get_random_tile_in_bounds(quadrant_bounds, "wall")
            if start_node is None:
                start_node = self._get_random_tile_in_bounds(
                    quadrant_bounds, "potential_floor"
                )
            if start_node is None or start_node in self.portals_on_floor:
                continue

            all_floor_tiles = self._collect_floor_tiles()
            non_portal_floor_tiles = [
                f for f in all_floor_tiles if f not in self.portals_on_floor
            ]

            end_node_choices = (
                non_portal_floor_tiles if non_portal_floor_tiles else all_floor_tiles
            )
            if not end_node_choices:
                end_node_choices = [player_start_pos]

            end_node = random.choice(end_node_choices)
            if end_node == start_node and len(end_node_choices) > 1:
                potential_end_nodes = [
                    fn for fn in end_node_choices if fn != start_node
                ]
                if potential_end_nodes:
                    end_node = random.choice(potential_end_nodes)

            self._perform_directed_random_walk(start_node, end_node)

    def _generate_path_network_respecting_portals(
        self,
        player_start_pos: tuple[int, int],
        original_win_pos: tuple[int, int],
    ):
        base_sum = self.width + self.height
        min_paths, max_paths = (
            (1, max(1, base_sum // 10))
            if self.floor_portion < 0.35
            else (
                max(1, base_sum // 10),
                max(max(1, base_sum // 10), base_sum // 5),
            )
        )
        num_additional_paths = random.randint(min_paths, max_paths)

        potential_target_tiles = []
        for y_coord in range(1, self.height - 1):
            for x_coord in range(1, self.width - 1):
                coord = (x_coord, y_coord)
                if coord in self.portals_on_floor:
                    continue
                tile = self.world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "potential_floor":
                    potential_target_tiles.append(coord)

        if player_start_pos in potential_target_tiles:
            potential_target_tiles.remove(player_start_pos)
        if original_win_pos in potential_target_tiles:
            potential_target_tiles.remove(original_win_pos)

        for _ in range(num_additional_paths):
            if not potential_target_tiles:
                break
            target_pos = potential_target_tiles.pop(
                random.randrange(len(potential_target_tiles))
            )

            current_floor_tiles = self._collect_floor_tiles()
            non_portal_origins = [
                t for t in current_floor_tiles if t not in self.portals_on_floor
            ]
            origin_choices = (
                non_portal_origins if non_portal_origins else current_floor_tiles
            )
            if not origin_choices:
                origin_choices = [player_start_pos]

            origin_pos = random.choice(origin_choices)

            self.path_finder.carve_bresenham_line(
                self.world_map,
                origin_pos,
                target_pos,
                self.width,
                self.height,
                protected_coords=self.portals_on_floor,
            )

    def _collect_floor_tiles(self) -> List[tuple[int, int]]:
        return [
            (x_coord, y_coord)
            for y_coord in range(1, self.height - 1)
            for x_coord in range(1, self.width - 1)
            if (t := self.world_map.get_tile(x_coord, y_coord)) and t.type == "floor"
        ]

    def _try_place_random_entity(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        if (
            not (t := self.world_map.get_tile(x, y))
            or t.item
            or t.monster
            or t.is_portal
        ):
            return False
        if random.random() < 0.25:
            if random.random() < 0.6:
                it = random.choice(
                    [
                        (
                            "Health Potion",
                            "Restores some HP.",
                            {"type": "heal", "amount": 10},
                        ),
                        (
                            "Dagger",
                            "A small blade.",
                            {"type": "weapon", "attack_bonus": 2, "verb": "stabs"},
                        ),
                    ]
                )
                self.world_map.place_item(Item(it[0], it[1], it[2]), x, y)
            else:
                mt = random.choice([("Goblin", 10, 3), ("Bat", 5, 2)])
                self.world_map.place_monster(
                    Monster(mt[0], mt[1], mt[2], x=x, y=y), x, y
                )
            return True
        return False

    def _place_additional_entities_respecting_portals(
        self,
        floor_tiles: List[tuple[int, int]],
        player_start_pos: tuple[int, int],
        poi_pos: tuple[int, int],
    ):
        if not floor_tiles:
            return
        npt = (self.width * self.height) // 15
        av_t = [
            t
            for t in floor_tiles
            if t != player_start_pos and t != poi_pos and t not in self.portals_on_floor
        ]
        random.shuffle(av_t)
        for _ in range(npt):
            if not av_t:
                break
            self._try_place_random_entity(av_t.pop())

    def _select_start_and_win_positions_avoiding_portals(
        self,
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        potential_spots = []
        for r_idx in range(1, self.height - 1):
            for c_idx in range(1, self.width - 1):
                if (c_idx, r_idx) not in self.portals_on_floor:
                    potential_spots.append((c_idx, r_idx))

        if len(potential_spots) < 2:
            fallback_spots = [(1, 1), (1, 2), (2, 1), (2, 2)]
            potential_spots = []
            for fx, fy in fallback_spots:
                if (
                    1 <= fx < self.width - 1
                    and 1 <= fy < self.height - 1
                    and (fx, fy) not in self.portals_on_floor
                ):
                    potential_spots.append((fx, fy))
            if len(potential_spots) < 2:
                error_msg = f"Cannot select start/POI. Map: {self.width}x{self.height}"
                raise ValueError(
                    f"{error_msg}, {len(self.portals_on_floor)} portals, "
                    f"{len(potential_spots)} spots."
                )

        player_start_pos = random.choice(potential_spots)
        temp_win_pos_choices = [p for p in potential_spots if p != player_start_pos]
        if not temp_win_pos_choices:
            original_win_pos = player_start_pos
        else:
            original_win_pos = random.choice(temp_win_pos_choices)

        self.world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
        self.world_map.set_tile_type(original_win_pos[0], original_win_pos[1], "floor")
        return player_start_pos, original_win_pos

    def _convert_potential_floor_to_walls_respecting_portals(self):
        for y_coord in range(1, self.height - 1):
            for x_coord in range(1, self.width - 1):
                if (x_coord, y_coord) in self.portals_on_floor:
                    continue
                if (
                    tile := self.world_map.get_tile(x_coord, y_coord)
                ) and tile.type == "potential_floor":
                    self.world_map.set_tile_type(x_coord, y_coord, "wall")

    def _ensure_all_floor_tiles_reachable_from_start(
        self, floor_start_pos: tuple[int, int]
    ) -> None:
        original_start_pos_info = None
        start_tile = self.world_map.get_tile(floor_start_pos[0], floor_start_pos[1])

        if start_tile and start_tile.is_portal:
            original_start_pos_info = {
                "type": start_tile.type,
                "is_portal": start_tile.is_portal,
                "portal_to_floor_id": start_tile.portal_to_floor_id,
            }
            self.world_map.set_tile_type(
                floor_start_pos[0], floor_start_pos[1], "floor"
            )
        elif not start_tile or start_tile.type != "floor":
            self.world_map.set_tile_type(
                floor_start_pos[0], floor_start_pos[1], "floor"
            )

        all_current_floor_tiles = self._collect_floor_tiles()

        if not all_current_floor_tiles:
            if original_start_pos_info:
                tile_to_restore = self.world_map.get_tile(
                    floor_start_pos[0], floor_start_pos[1]
                )
                if tile_to_restore:
                    tile_to_restore.type = original_start_pos_info["type"]
                    tile_to_restore.is_portal = original_start_pos_info["is_portal"]
                    tile_to_restore.portal_to_floor_id = original_start_pos_info[
                        "portal_to_floor_id"
                    ]
            return

        reachable_floor_set = self.connectivity_manager.get_reachable_floor_tiles(
            self.world_map, [floor_start_pos], self.width, self.height
        )

        for x_coord, y_coord in all_current_floor_tiles:
            if (x_coord, y_coord) not in reachable_floor_set:
                if (
                    x_coord,
                    y_coord,
                ) == floor_start_pos and original_start_pos_info:
                    pass
                else:
                    current_tile_check = self.world_map.get_tile(x_coord, y_coord)
                    if not (current_tile_check and current_tile_check.is_portal):
                        self.world_map.set_tile_type(x_coord, y_coord, "wall")

        if original_start_pos_info:
            tile_to_restore = self.world_map.get_tile(
                floor_start_pos[0], floor_start_pos[1]
            )
            if tile_to_restore:
                tile_to_restore.type = original_start_pos_info["type"]
                tile_to_restore.is_portal = original_start_pos_info["is_portal"]
                tile_to_restore.portal_to_floor_id = original_start_pos_info[
                    "portal_to_floor_id"
                ]

    def build(self) -> Tuple[WorldMap, Tuple[int, int], Tuple[int, int]]:
        if self.width < 10 or self.height < 10:
            raise ValueError(
                f"Map too small for single floor generation. Minimum size is 10x10, "
                f"got {self.width}x{self.height}"
            )

        for r_idx in range(1, self.height - 1):
            for c_idx in range(1, self.width - 1):
                if (tile := self.world_map.get_tile(c_idx, r_idx)) and tile.is_portal:
                    self.portals_on_floor.append((c_idx, r_idx))
                    self.portal_destinations[(c_idx, r_idx)] = tile.portal_to_floor_id

        floor_start, floor_poi = self._select_start_and_win_positions_avoiding_portals()

        if not (st_tile := self.world_map.get_tile(floor_start[0], floor_start[1])) or (
            st_tile.type != "floor" and not st_tile.is_portal
        ):
            self.world_map.set_tile_type(floor_start[0], floor_start[1], "floor")

        points_to_connect_to_start = [floor_poi] + self.portals_on_floor
        for point in points_to_connect_to_start:
            target_tile = self.world_map.get_tile(point[0], point[1])
            is_target_portal = point in self.portals_on_floor
            original_dest_if_portal = (
                self.portal_destinations.get(point) if is_target_portal else None
            )
            current_target_type = target_tile.type if target_tile else "wall"  # type: ignore

            if current_target_type != "floor":
                self.world_map.set_tile_type(point[0], point[1], "floor")

            self.path_finder.carve_bresenham_line(
                self.world_map,
                floor_start,
                point,
                self.width,
                self.height,
                protected_coords=self.portals_on_floor,
            )

            if is_target_portal:
                restored_tile = self.world_map.get_tile(point[0], point[1])
                if restored_tile:
                    restored_tile.type = "portal"
                    restored_tile.is_portal = True
                    restored_tile.portal_to_floor_id = original_dest_if_portal
            elif current_target_type != "floor":
                tile_at_point = self.world_map.get_tile(point[0], point[1])
                if (
                    tile_at_point.type == "floor"
                    and current_target_type != "potential_floor"
                ):  # type: ignore
                    pass
                else:
                    if not (tile_at_point and tile_at_point.is_portal):
                        self.world_map.set_tile_type(
                            point[0],
                            point[1],
                            current_target_type  # type: ignore
                            if current_target_type != "potential_floor"  # type: ignore
                            else "wall",
                        )

        self._perform_random_walks_respecting_portals(floor_start)
        self._generate_path_network_respecting_portals(floor_start, floor_poi)
        self._convert_potential_floor_to_walls_respecting_portals()

        self.density_adjuster.adjust_density(
            self.world_map,
            floor_start,
            floor_poi,
            self.width,
            self.height,
            self.floor_portion,
            protected_coords=self.portals_on_floor,
        )
        self.connectivity_manager.ensure_connectivity(
            self.world_map,
            floor_start,
            self.width,
            self.height,
            protected_coords=self.portals_on_floor,
        )

        for point in self.portals_on_floor:
            original_dest_if_portal = self.portal_destinations.get(point)
            self.path_finder.carve_bresenham_line(
                self.world_map,
                floor_start,
                point,
                self.width,
                self.height,
                protected_coords=self.portals_on_floor,
            )
            restored_tile = self.world_map.get_tile(point[0], point[1])
            if restored_tile:
                restored_tile.type = "portal"
                restored_tile.is_portal = True
                restored_tile.portal_to_floor_id = original_dest_if_portal

        self._ensure_all_floor_tiles_reachable_from_start(floor_start)

        final_floor_tiles = self._collect_floor_tiles()
        self._place_additional_entities_respecting_portals(
            final_floor_tiles,
            floor_start,
            floor_poi,
        )

        return self.world_map, floor_start, floor_poi

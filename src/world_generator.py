import random
from collections import deque
from typing import Optional, List # Ensure List is imported for type hints

from src.item import Item
from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.density import FloorDensityAdjuster
from src.map_algorithms.pathfinding import PathFinder
from src.monster import Monster
from src.world_map import WorldMap


class WorldGenerator:
    DEFAULT_FLOOR_PORTION = 0.5

    def __init__(self, floor_portion: Optional[float] = None):
        self.floor_portion = floor_portion if floor_portion is not None else self.DEFAULT_FLOOR_PORTION
        self.connectivity_manager = MapConnectivityManager()
        self.density_adjuster = FloorDensityAdjuster(self.connectivity_manager)
        self.path_finder = PathFinder()

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
        if min_x > max_x: max_x = min_x
        if min_y > max_y: max_y = min_y
        return min_x, min_y, max_x, max_y

    def _initialize_map(self, width: int, height: int, seed: Optional[int]) -> WorldMap:
        if seed is not None: random.seed(seed)
        world_map = WorldMap(width, height)
        for y_coord in range(height):
            for x_coord in range(width):
                if x_coord == 0 or x_coord == width - 1 or y_coord == 0 or y_coord == height - 1:
                    world_map.set_tile_type(x_coord, y_coord, "wall")
                else:
                    world_map.set_tile_type(x_coord, y_coord, "potential_floor")
        return world_map

    def _select_start_and_win_positions(
        self, width: int, height: int, world_map: WorldMap
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        if (width < 3 or height < 4) and (width < 4 or height < 3):
            raise ValueError("Map dimensions must be at least 3x4 or 4x3...")
        player_start_x = random.randint(1, width - 2)
        player_start_y = random.randint(1, height - 2)
        win_x, win_y = random.randint(1, width - 2), random.randint(1, height - 2)
        player_start_pos = (player_start_x, player_start_y)
        original_win_pos = (win_x, win_y)
        attempts = 0
        max_attempts = ((width - 2) * (height - 2)) // 2 + 1
        if max_attempts <= 0: max_attempts = 1
        while original_win_pos == player_start_pos:
            if attempts >= max_attempts:
                if (width - 2) * (height - 2) == 1: break
                break
            win_x, win_y = random.randint(1, width - 2), random.randint(1, height - 2)
            original_win_pos = (win_x, win_y)
            attempts += 1
        world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
        world_map.set_tile_type(original_win_pos[0], original_win_pos[1], "floor")
        return player_start_pos, original_win_pos

    def _get_random_tile_in_bounds(
        self, world_map: WorldMap, bounds: tuple[int, int, int, int],
        tile_type: str, max_attempts: int = 100,
    ) -> Optional[tuple[int, int]]:
        min_x, min_y, max_x, max_y = bounds
        if min_x > max_x or min_y > max_y: return None
        for _ in range(max_attempts):
            if max_x < min_x or max_y < min_y: return None
            rand_x, rand_y = random.randint(min_x, max_x), random.randint(min_y, max_y)
            if (tile := world_map.get_tile(rand_x, rand_y)) and tile.type == tile_type:
                return rand_x, rand_y
        return None

    def _perform_directed_random_walk(
        self, world_map: WorldMap, start_pos: tuple[int, int], end_pos: tuple[int, int],
        map_width: int, map_height: int, portals_on_floor: Optional[List[tuple[int,int]]] = None # Corrected type hint
    ):
        portals_on_floor = portals_on_floor or []
        current_x, current_y = start_pos
        if (current_x, current_y) not in portals_on_floor:
            world_map.set_tile_type(current_x, current_y, "floor")

        last_dx, last_dy = 0,0
        current_walk_max_steps = 75
        if self.floor_portion < 0.35: current_walk_max_steps = 40
        path_history = [(current_x, current_y)]
        stuck_count = 0; max_stuck_attempts = 5

        for _ in range(current_walk_max_steps):
            if (current_x, current_y) == end_pos: break
            dx_target, dy_target = end_pos[0] - current_x, end_pos[1] - current_y
            possible_directions = []
            for d_dx, d_dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                if 1 <= current_x + d_dx < map_width - 1 and \
                   1 <= current_y + d_dy < map_height - 1:
                    possible_directions.append((d_dx, d_dy))
            if not possible_directions: break

            preferred_directions = []
            if dy_target < 0 and (0,-1) in possible_directions: preferred_directions.append((0,-1))
            if dy_target > 0 and (0,1) in possible_directions: preferred_directions.append((0,1))
            if dx_target < 0 and (-1,0) in possible_directions: preferred_directions.append((-1,0))
            if dx_target > 0 and (1,0) in possible_directions: preferred_directions.append((1,0))

            chosen_dx, chosen_dy = random.choice(possible_directions) if possible_directions else (0,0)
            if preferred_directions and random.random() < 0.75:
                chosen_dx, chosen_dy = random.choice(preferred_directions)

            if (last_dx,last_dy) != (0,0) and (last_dx,last_dy) in possible_directions and random.random() < 0.6:
                chosen_dx, chosen_dy = last_dx, last_dy

            if chosen_dx == 0 and chosen_dy == 0 and not possible_directions : break

            next_x, next_y = current_x + chosen_dx, current_y + chosen_dy
            last_dx, last_dy = chosen_dx, chosen_dy

            if (next_x, next_y) not in portals_on_floor:
                if (tile := world_map.get_tile(next_x,next_y)) and \
                   (tile.type=="wall" or tile.type=="potential_floor"):
                    world_map.set_tile_type(next_x,next_y,"floor")

            current_x, current_y = next_x, next_y
            path_history.append((current_x,current_y))

            if len(path_history)>1 and (current_x,current_y) != path_history[-2]:stuck_count=0
            else:stuck_count+=1
            if stuck_count>=max_stuck_attempts and len(path_history)>1:
                for _ in range(min(3,len(path_history)-1)):
                    if len(path_history)>1:path_history.pop()
                if path_history:current_x,current_y=path_history[-1]
                stuck_count=0

    def _perform_random_walks_respecting_portals(self, world_map: WorldMap, player_start_pos: tuple[int,int],
                                                 map_width: int, map_height: int, portals_on_floor: List[tuple[int,int]]): # Corrected type hint
        for quadrant_index in range(4):
            quadrant_bounds = self._get_quadrant_bounds(quadrant_index, map_width, map_height)
            if quadrant_bounds[0] > quadrant_bounds[2] or quadrant_bounds[1] > quadrant_bounds[3]: continue

            start_node = self._get_random_tile_in_bounds(world_map, quadrant_bounds, "wall")
            if start_node is None:
                start_node = self._get_random_tile_in_bounds(world_map, quadrant_bounds, "potential_floor")
            if start_node is None or start_node in portals_on_floor:
                continue

            all_floor_tiles = self._collect_floor_tiles(world_map, map_width, map_height)
            non_portal_floor_tiles = [f for f in all_floor_tiles if f not in portals_on_floor]

            end_node_choices = non_portal_floor_tiles if non_portal_floor_tiles else all_floor_tiles
            if not end_node_choices : end_node_choices = [player_start_pos]

            end_node = random.choice(end_node_choices)
            if end_node == start_node and len(end_node_choices) > 1:
                potential_end_nodes = [fn for fn in end_node_choices if fn != start_node]
                if potential_end_nodes: end_node = random.choice(potential_end_nodes)

            self._perform_directed_random_walk(world_map, start_node, end_node, map_width, map_height, portals_on_floor)


    def _generate_path_network_respecting_portals(self, world_map: WorldMap, player_start_pos: tuple[int,int],
                                                original_win_pos: tuple[int,int], map_width: int, map_height: int,
                                                portals_on_floor: List[tuple[int,int]]): # Corrected type hint
        base_sum = map_width + map_height
        min_paths, max_paths = (1, max(1, base_sum//10)) if self.floor_portion < 0.35 else \
                               (max(1, base_sum//10), max(max(1,base_sum//10), base_sum//5))
        num_additional_paths = random.randint(min_paths, max_paths)

        potential_target_tiles = []
        for y_coord in range(1, map_height - 1):
            for x_coord in range(1, map_width - 1):
                coord = (x_coord, y_coord)
                if coord in portals_on_floor: continue
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "potential_floor":
                    potential_target_tiles.append(coord)

        if player_start_pos in potential_target_tiles: potential_target_tiles.remove(player_start_pos)
        if original_win_pos in potential_target_tiles: potential_target_tiles.remove(original_win_pos)

        for _ in range(num_additional_paths):
            if not potential_target_tiles: break
            target_pos = potential_target_tiles.pop(random.randrange(len(potential_target_tiles)))

            current_floor_tiles = self._collect_floor_tiles(world_map, map_width, map_height)
            non_portal_origins = [t for t in current_floor_tiles if t not in portals_on_floor]
            origin_choices = non_portal_origins if non_portal_origins else current_floor_tiles
            if not origin_choices: origin_choices = [player_start_pos]

            origin_pos = random.choice(origin_choices)

            self.path_finder.carve_bresenham_line(world_map, origin_pos, target_pos, map_width, map_height, protected_coords=portals_on_floor)


    def _collect_floor_tiles( self, world_map: WorldMap, map_width: int, map_height: int ) -> List[tuple[int, int]]: # Corrected type hint
        return [(x_coord,y_coord) for y_coord in range(1,map_height-1) for x_coord in range(1,map_width-1)
                if (t:=world_map.get_tile(x_coord,y_coord)) and t.type=="floor"]

    def _place_win_item_at_furthest_point( # This is for single floor POI, not final Amulet
        self, world_map: WorldMap, player_start_pos: tuple[int, int],
        map_width: int, map_height: int, floor_tiles: List[tuple[int, int]], # Corrected type hint
        portals_on_floor: Optional[List[tuple[int,int]]] = None # Corrected type hint
    ) -> tuple[int, int]:
        portals_on_floor = portals_on_floor or []

        valid_floor_tiles = [ft for ft in floor_tiles if ft not in portals_on_floor]

        if not valid_floor_tiles:
            if player_start_pos not in portals_on_floor:
                awp = player_start_pos
                if not (t:=world_map.get_tile(awp[0],awp[1])) or (t.type!="floor" and not t.is_portal):
                     world_map.set_tile_type(awp[0],awp[1],"floor")
                return awp
            else:
                  return (map_width//2, map_height//2) if map_width > 2 and map_height > 2 else (1,1)

        bfs_start_node = player_start_pos
        start_node_tile = world_map.get_tile(bfs_start_node[0], bfs_start_node[1])
        if not start_node_tile or (start_node_tile.type != "floor" and not start_node_tile.is_portal):
            world_map.set_tile_type(bfs_start_node[0], bfs_start_node[1], "floor")
        elif start_node_tile.is_portal:
            adj_floor_found = False
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                nx,ny = bfs_start_node[0]+dx, bfs_start_node[1]+dy
                if (adj_t := world_map.get_tile(nx,ny)) and adj_t.type == "floor" and (nx,ny) not in portals_on_floor:
                    bfs_start_node = (nx,ny); adj_floor_found = True; break
            if not adj_floor_found:
                if valid_floor_tiles: bfs_start_node = random.choice(valid_floor_tiles)
                else: return (map_width//2, map_height//2)

        awp = self.path_finder.find_furthest_point(world_map, bfs_start_node, map_width, map_height)

        chosen_tile = world_map.get_tile(awp[0], awp[1])
        if not chosen_tile or chosen_tile.type != "floor" or (awp[0],awp[1]) in portals_on_floor:
            available_spots = [tile for tile in valid_floor_tiles if tile != player_start_pos]
            if available_spots: awp = random.choice(available_spots)
            elif player_start_pos in valid_floor_tiles and player_start_pos not in portals_on_floor: awp = player_start_pos
            else:
                if player_start_pos not in portals_on_floor:
                    awp = player_start_pos
                    if not (t:=world_map.get_tile(awp[0],awp[1])) or (t.type!="floor" and not t.is_portal):
                         world_map.set_tile_type(awp[0],awp[1],"floor")
                else:
                      return (map_width//2, map_height//2) if valid_floor_tiles else player_start_pos
        return awp


    def _try_place_random_entity(self, world_map: WorldMap, pos: tuple[int, int]) -> bool:
        x,y=pos
        if not (t:=world_map.get_tile(x,y))or t.item or t.monster or t.is_portal:return False
        if random.random()<0.25:
            if random.random()<0.6:
                it=random.choice([("Health Potion","Restores some HP.",{"type":"heal","amount":10}),
                                  ("Dagger","A small blade.",{"type":"weapon","attack_bonus":2,"verb":"stabs"})])
                world_map.place_item(Item(it[0],it[1],it[2]),x,y)
            else:
                mt=random.choice([("Goblin",10,3),("Bat",5,2)])
                world_map.place_monster(Monster(mt[0],mt[1],mt[2],x=x,y=y),x,y)
            return True
        return False

    def _place_additional_entities_respecting_portals(
        self, world_map: WorldMap, floor_tiles: List[tuple[int, int]], # Corrected type hint
        player_start_pos: tuple[int, int], poi_pos: tuple[int, int],
        map_width: int, map_height: int, portals_on_floor: List[tuple[int,int]] # Corrected type hint
    ):
        if not floor_tiles:return
        npt=(map_width*map_height)//15
        av_t=[t for t in floor_tiles if t!=player_start_pos and t!=poi_pos and t not in portals_on_floor]
        random.shuffle(av_t)
        for _ in range(npt):
            if not av_t:break
            self._try_place_random_entity(world_map,av_t.pop())


    def _select_start_and_win_positions_avoiding_portals(
        self, width: int, height: int, world_map: WorldMap, existing_portals: List[tuple[int,int]] # Corrected type hint
    ) -> tuple[tuple[int, int], tuple[int, int]]:

        potential_spots = []
        for r_idx in range(1, height - 1):
            for c_idx in range(1, width - 1):
                if (c_idx,r_idx) not in existing_portals:
                    potential_spots.append((c_idx,r_idx))

        if len(potential_spots) < 2:
            fallback_spots = [(1,1), (1,2), (2,1), (2,2)]
            potential_spots = []
            for fx, fy in fallback_spots:
                if 1 <= fx < width -1 and 1 <= fy < height -1 and (fx,fy) not in existing_portals:
                    potential_spots.append((fx,fy))
            if len(potential_spots) < 2:
                raise ValueError(f"Cannot select distinct start/POI. Map size {width}x{height}, {len(existing_portals)} portals, only {len(potential_spots)} non-portal spots.")

        player_start_pos = random.choice(potential_spots)
        temp_win_pos_choices = [p for p in potential_spots if p != player_start_pos]
        if not temp_win_pos_choices:
            original_win_pos = player_start_pos
        else:
            original_win_pos = random.choice(temp_win_pos_choices)

        world_map.set_tile_type(player_start_pos[0],player_start_pos[1],"floor")
        world_map.set_tile_type(original_win_pos[0],original_win_pos[1],"floor")
        return player_start_pos, original_win_pos


    def _generate_single_floor(
        self, width: int, height: int, current_seed: Optional[int] = None,
        existing_map: Optional[WorldMap] = None
    ) -> tuple[WorldMap, tuple[int, int], tuple[int, int]]:
        if (width<3 or height<4)and(width<4 or height<3):raise ValueError("Map too small for gen single floor")
        if current_seed is not None:random.seed(current_seed)

        world_map = existing_map if existing_map else self._initialize_map(width, height, None)

        portals_on_this_floor = []
        portal_destinations = {}
        for r_idx in range(1, height - 1):
            for c_idx in range(1, width - 1):
                if (tile := world_map.get_tile(c_idx, r_idx)) and tile.is_portal:
                    portals_on_this_floor.append((c_idx, r_idx))
                    portal_destinations[(c_idx,r_idx)] = tile.portal_to_floor_id


        floor_start, floor_poi = self._select_start_and_win_positions_avoiding_portals(
            width, height, world_map, portals_on_this_floor
        )

        if not (st_tile := world_map.get_tile(floor_start[0],floor_start[1])) or \
           (st_tile.type != "floor" and not st_tile.is_portal):
            world_map.set_tile_type(floor_start[0],floor_start[1],"floor")

        points_to_connect_to_start = [floor_poi] + portals_on_this_floor
        for point in points_to_connect_to_start:
            target_tile = world_map.get_tile(point[0], point[1])
            is_target_portal = point in portals_on_this_floor
            original_dest_if_portal = portal_destinations.get(point) if is_target_portal else None
            current_target_type = target_tile.type if target_tile else "wall"

            if current_target_type != "floor":
                 world_map.set_tile_type(point[0],point[1],"floor")

            self.path_finder.carve_bresenham_line(world_map, floor_start, point, width, height, protected_coords=portals_on_this_floor)

            if is_target_portal:
                restored_tile = world_map.get_tile(point[0],point[1])
                if restored_tile:
                     restored_tile.type="portal"; restored_tile.is_portal=True
                     restored_tile.portal_to_floor_id = original_dest_if_portal
            elif current_target_type != "floor":
                 if world_map.get_tile(point[0],point[1]).type == "floor" and current_target_type != "potential_floor":
                      pass
                 else:
                      if not (world_map.get_tile(point[0],point[1]) and world_map.get_tile(point[0],point[1]).is_portal):
                           world_map.set_tile_type(point[0],point[1], current_target_type if current_target_type != "potential_floor" else "wall")


        self._perform_random_walks_respecting_portals(world_map,floor_start,width,height,portals_on_this_floor)
        self._generate_path_network_respecting_portals(world_map,floor_start,floor_poi,width,height,portals_on_this_floor)
        self._convert_potential_floor_to_walls_respecting_portals(world_map,width,height,portals_on_this_floor)

        self.density_adjuster.adjust_density(
            world_map, floor_start, floor_poi, width, height,
            self.floor_portion, protected_coords=portals_on_this_floor
        )
        self.connectivity_manager.ensure_connectivity(
            world_map, floor_start, width, height,
            protected_coords=portals_on_this_floor
        )

        for point in portals_on_this_floor:
            original_dest_if_portal = portal_destinations.get(point)
            self.path_finder.carve_bresenham_line(world_map, floor_start, point, width, height, protected_coords=portals_on_this_floor)
            restored_tile = world_map.get_tile(point[0],point[1])
            if restored_tile:
                 restored_tile.type="portal"; restored_tile.is_portal=True
                 restored_tile.portal_to_floor_id = original_dest_if_portal

        self._ensure_all_floor_tiles_reachable_from_start(world_map,floor_start,width,height)

        final_floor_tiles=self._collect_floor_tiles(world_map,width,height)
        self._place_additional_entities_respecting_portals(world_map,final_floor_tiles,floor_start,floor_poi,width,height, portals_on_this_floor)

        return world_map, floor_start, floor_poi


    def _print_debug_map(self, world_map: WorldMap, width: int, height: int, highlight_coords: Optional[List[tuple[int,int]]] = None) -> None: # Corrected type hint
        print(f"--- Debug Map {width}x{height} ---")
        highlights = highlight_coords or []
        for y_coord in range(height):
            row_str = ""
            for x_coord in range(width):
                char = "?"
                if (tile := world_map.get_tile(x_coord,y_coord)):
                    if (x_coord,y_coord) in highlights: char = "*"
                    elif tile.is_portal: char = "P"
                    elif tile.type == "wall": char = "#"
                    elif tile.type == "floor": char = "."
                    elif tile.type == "potential_floor": char = "~"
                row_str += char + " "
            print(row_str)
        print("----------------------")

    def _convert_potential_floor_to_walls_respecting_portals(self, world_map: WorldMap, width: int, height: int, portals: List[tuple[int,int]]): # Corrected type hint
        for y_coord in range(1, height - 1):
            for x_coord in range(1, width - 1):
                if (x_coord,y_coord) in portals: continue
                if (tile := world_map.get_tile(x_coord,y_coord)) and tile.type == "potential_floor":
                    world_map.set_tile_type(x_coord,y_coord,"wall")


    def _ensure_all_floor_tiles_reachable_from_start(
        self, world_map: WorldMap, floor_start_pos: tuple[int,int], width: int, height: int
    ) -> None:
        original_start_pos_info = None
        start_tile = world_map.get_tile(floor_start_pos[0], floor_start_pos[1])

        if start_tile and start_tile.is_portal:
            original_start_pos_info = {
                "type": start_tile.type,
                "is_portal": start_tile.is_portal,
                "portal_to_floor_id": start_tile.portal_to_floor_id
            }
            world_map.set_tile_type(floor_start_pos[0], floor_start_pos[1], "floor")
        elif not start_tile or start_tile.type != "floor":
             world_map.set_tile_type(floor_start_pos[0], floor_start_pos[1], "floor")

        all_current_floor_tiles = self._collect_floor_tiles(world_map, width, height)

        if not all_current_floor_tiles:
            if original_start_pos_info:
                tile_to_restore = world_map.get_tile(floor_start_pos[0], floor_start_pos[1])
                if tile_to_restore:
                    tile_to_restore.type = original_start_pos_info["type"]
                    tile_to_restore.is_portal = original_start_pos_info["is_portal"]
                    tile_to_restore.portal_to_floor_id = original_start_pos_info["portal_to_floor_id"]
            return

        reachable_floor_set = self.connectivity_manager.get_reachable_floor_tiles(
            world_map, [floor_start_pos], width, height
        )

        for x_coord, y_coord in all_current_floor_tiles:
            if (x_coord, y_coord) not in reachable_floor_set:
                if (x_coord, y_coord) == floor_start_pos and original_start_pos_info:
                    pass
                else:
                    current_tile_check = world_map.get_tile(x_coord, y_coord)
                    if not (current_tile_check and current_tile_check.is_portal):
                        world_map.set_tile_type(x_coord, y_coord, "wall")

        if original_start_pos_info:
            tile_to_restore = world_map.get_tile(floor_start_pos[0], floor_start_pos[1])
            if tile_to_restore:
                tile_to_restore.type = original_start_pos_info["type"]
                tile_to_restore.is_portal = original_start_pos_info["is_portal"]
                tile_to_restore.portal_to_floor_id = original_start_pos_info["portal_to_floor_id"]

    def _ensure_portal_connectivity(
        self, world_maps: dict[int, WorldMap], width: int, height: int,
        floor_details_list: list[dict],
        common_portal_coords: List[tuple[int,int]], # Corrected type hint
        main_seed_for_debug: Optional[int] = None
    ) -> None:
        num_floors = len(world_maps)
        if num_floors <= 1 or not common_portal_coords: return

        taken_portal_coords_globally: set[tuple[int,int]] = set()
        parent = list(range(num_floors))
        def find_set(i):
            if parent[i]==i: return i
            parent[i]=find_set(parent[i]); return parent[i]
        def unite_sets(i,j):
            r_i,r_j=find_set(i),find_set(j)
            if r_i!=r_j: parent[r_i]=r_j; return True
            return False

        available_common_coords = list(common_portal_coords)
        random.shuffle(available_common_coords)

        for i in range(num_floors):
            f1_id, f2_id = i, (i+1)%num_floors
            if find_set(f1_id) == find_set(f2_id) and num_floors > 2 : continue
            if not available_common_coords: break
            p_x, p_y = available_common_coords.pop(0)
            t1 = world_maps[f1_id].get_tile(p_x,p_y)
            t2 = world_maps[f2_id].get_tile(p_x,p_y)
            if t1 and t2:
                t1.type, t1.is_portal, t1.portal_to_floor_id = "portal",True,f2_id
                t2.type, t2.is_portal, t2.portal_to_floor_id = "portal",True,f1_id
                unite_sets(f1_id, f2_id)
                taken_portal_coords_globally.add((p_x,p_y))
            else: available_common_coords.append((p_x,p_y))

        num_c = sum(1 for i in range(num_floors) if parent[i]==i)
        attempts = 0; max_attempts = num_floors * 2
        while num_c > 1 and attempts < max_attempts:
            attempts+=1
            if not available_common_coords: break
            roots = [r for r in range(num_floors) if parent[r]==r]
            if len(roots) < 2: break
            r1c,r2c = random.sample(roots,2)
            comp1_f=[fid for fid in range(num_floors) if find_set(fid)==r1c]
            comp2_f=[fid for fid in range(num_floors) if find_set(fid)==r2c]
            if not comp1_f or not comp2_f: continue
            f1l,f2l=random.choice(comp1_f),random.choice(comp2_f)
            if not available_common_coords: break
            px2,py2 = available_common_coords.pop(0)
            t1n,t2n = world_maps[f1l].get_tile(px2,py2), world_maps[f2l].get_tile(px2,py2)
            if t1n and t2n:
                t1n.type,t1n.is_portal,t1n.portal_to_floor_id="portal",True,f2l
                t2n.type,t2n.is_portal,t2n.portal_to_floor_id="portal",True,f1l
                unite_sets(f1l,f2l);taken_portal_coords_globally.add((px2,py2))
                num_c=sum(1 for i_comp in range(num_floors)if parent[i_comp]==i_comp)
            else: available_common_coords.append((px2,py2))
        if sum(1 for i_loop in range(num_floors)if parent[i_loop]==i_loop)>1:
            print(f"Warning: WG could not connect all floors using common coords.")

    def generate_world(
        self, width: int, height: int, seed: Optional[int] = None
    ) -> tuple[dict[int, WorldMap], tuple[int, int, int], tuple[int, int, int], list[dict]]:
        if seed is not None: random.seed(seed)

        num_floors = random.randint(2,10)
        world_maps: dict[int,WorldMap] = {}
        floor_details_list = []

        num_common_portal_coords = min(5, ((width-2)*(height-2)) // 20 + 1 if width>2 and height>2 else 1)
        if num_common_portal_coords < 1 and (width-2)*(height-2) > 0 : num_common_portal_coords = 1

        common_portal_coords: List[tuple[int,int]] = [] # Corrected type hint
        if width > 2 and height > 2:
            possible_inner_coords = [(x,y) for x in range(1,width-1) for y in range(1,height-1)]
            if possible_inner_coords:
                 random.shuffle(possible_inner_coords)
                 common_portal_coords = possible_inner_coords[:num_common_portal_coords]

        for floor_id in range(num_floors):
            init_map_seed = random.randint(0, 2**32 - 1) if seed else None
            world_maps[floor_id] = self._initialize_map(width, height, seed=init_map_seed)
            floor_details_list.append({"id": floor_id, "map": world_maps[floor_id]})

        self._ensure_portal_connectivity(world_maps, width, height, floor_details_list, common_portal_coords, main_seed_for_debug=seed)

        for floor_id_gen in range(num_floors):
            current_map_obj = world_maps[floor_id_gen]
            single_floor_gen_seed = random.randint(0, 2**32 - 1) if seed else None
            if seed==777 and floor_id_gen==0:
                print(f"\n[DEBUG] Main seed 777, F0 single_floor_gen_seed={single_floor_gen_seed}") # Retained single debug print

            _, floor_start_pos, floor_poi_pos = self._generate_single_floor(
                width, height, current_seed=single_floor_gen_seed, existing_map=current_map_obj
            )

            for fd_item in floor_details_list:
                if fd_item["id"] == floor_id_gen:
                    fd_item["start"] = floor_start_pos
                    fd_item["poi"] = floor_poi_pos
                    break

        ps_fid=0
        player_start_detail = next((fd for fd in floor_details_list if fd["id"] == ps_fid),None)
        if not player_start_detail or "start" not in player_start_detail:
            ps_x,ps_y = (width//2 if width>0 else 0, height//2 if height>0 else 0)
            # print(f"Warning: Player start detail not found for floor {ps_fid}, using fallback {ps_x},{ps_y}") # Removed for less noise
        else: ps_x,ps_y=player_start_detail["start"]
        ps_full_pos=(ps_x,ps_y,ps_fid)

        am_fid=ps_fid
        if num_floors>1:
            paf=[f["id"]for f in floor_details_list if f["id"]!=ps_fid]
            am_fid=random.choice(paf)if paf else(ps_fid+1)%num_floors

        am_map=world_maps[am_fid]
        am_ft=self._collect_floor_tiles(am_map,width,height)

        amulet_floor_detail = next((fd for fd in floor_details_list if fd["id"] == am_fid), None)
        if not amulet_floor_detail or "poi" not in amulet_floor_detail:
            sna_s = (width//2 if width>0 else 0, height//2 if height>0 else 0)
            # print(f"Warning: Amulet floor POI not found for floor {am_fid}, using fallback {sna_s}") # Removed for less noise
        else: sna_s=amulet_floor_detail["poi"]

        am_ps_on_f=[(x,y)for x in range(1,width-1)for y in range(1,height-1)if(t:=am_map.get_tile(x,y))and t.is_portal]
        if am_ps_on_f:sna_s=random.choice(am_ps_on_f)
        elif not am_ft:am_map.set_tile_type(1,1,"floor");am_ft.append((1,1));sna_s=(1,1)

        actual_win_full_pos:tuple[int,int,int]
        if not am_ft:
            ax,ay=world_maps[ps_fid].width//2,world_maps[ps_fid].height//2
            world_maps[ps_fid].set_tile_type(ax,ay,"floor");actual_win_full_pos=(ax,ay,ps_fid)
        else:
            start_tile_for_amulet_find = am_map.get_tile(sna_s[0],sna_s[1])
            if not start_tile_for_amulet_find or \
               (start_tile_for_amulet_find.type!="floor" and not start_tile_for_amulet_find.is_portal):
                if am_ft : sna_s=random.choice(am_ft)
                else: sna_s = (1,1)

            amulet_x, amulet_y = self.path_finder.find_furthest_point(am_map,sna_s,width,height)
            actual_win_full_pos=(amulet_x,amulet_y,am_fid)

            final_amulet_tile_check = world_maps[actual_win_full_pos[2]].get_tile(actual_win_full_pos[0], actual_win_full_pos[1])
            if final_amulet_tile_check and final_amulet_tile_check.is_portal:
                alternative_spots = []
                for dx_alt, dy_alt in [(0,1),(0,-1),(1,0),(-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                    alt_x, alt_y = actual_win_full_pos[0] + dx_alt, actual_win_full_pos[1] + dy_alt
                    if 1 <= alt_x < width -1 and 1 <= alt_y < height -1:
                        alt_tile = world_maps[actual_win_full_pos[2]].get_tile(alt_x, alt_y)
                        if alt_tile and alt_tile.type == "floor" and not alt_tile.is_portal and alt_tile.item is None:
                            alternative_spots.append((alt_x, alt_y))

                if alternative_spots:
                    new_amulet_coord = random.choice(alternative_spots)
                    actual_win_full_pos = (new_amulet_coord[0], new_amulet_coord[1], actual_win_full_pos[2])
                else:
                    other_floor_tiles = [ft for ft in am_ft if not world_maps[actual_win_full_pos[2]].get_tile(ft[0],ft[1]).is_portal and \
                                           world_maps[actual_win_full_pos[2]].get_tile(ft[0],ft[1]).item is None and \
                                           world_maps[actual_win_full_pos[2]].get_tile(ft[0],ft[1]).type == "floor" ]
                    if other_floor_tiles:
                        new_amulet_coord = random.choice(other_floor_tiles)
                        actual_win_full_pos = (new_amulet_coord[0], new_amulet_coord[1], actual_win_full_pos[2])

        am_item=Item("Amulet of Yendor","Object of quest!",{"type":"quest"})
        target_amulet_map=world_maps[actual_win_full_pos[2]]
        wxf,wyf,_=actual_win_full_pos

        final_amulet_tile = target_amulet_map.get_tile(wxf,wyf)
        if not final_amulet_tile or (final_amulet_tile.type!="floor" and not final_amulet_tile.is_portal):
            target_amulet_map.set_tile_type(wxf,wyf,"floor")

        current_amulet_tile = target_amulet_map.get_tile(wxf,wyf)
        if current_amulet_tile and current_amulet_tile.item:target_amulet_map.remove_item(wxf,wyf)
        target_amulet_map.place_item(am_item,wxf,wyf)

        return world_maps,ps_full_pos,actual_win_full_pos,floor_details_list

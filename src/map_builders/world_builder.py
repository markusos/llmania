import random
from typing import List, Optional, Tuple

from src.item import Item
from src.map_builders.single_floor_builder import SingleFloorBuilder
from src.world_map import WorldMap


class WorldBuilder:
    def __init__(
        self, width: int, height: int, seed: Optional[int] = None, num_floors: int = 1
    ):
        self.width = width
        self.height = height
        self.seed = seed
        self.num_floors = num_floors
        self.world_maps: dict[int, WorldMap] = {}
        self.floor_details: list[dict] = []
        if self.seed is not None:
            random.seed(self.seed)

    def _initialize_world(self):
        num_common_portal_coords = (
            min(5, ((self.width - 2) * (self.height - 2)) // 20 + 1)
            if self.width > 2 and self.height > 2
            else 1
        )
        if num_common_portal_coords < 1 and (self.width - 2) * (self.height - 2) > 0:
            num_common_portal_coords = 1

        common_portal_coords: List[tuple[int, int]] = []
        if self.width > 2 and self.height > 2:
            possible_inner_coords = [
                (x, y)
                for x in range(1, self.width - 1)
                for y in range(1, self.height - 1)
            ]
            if possible_inner_coords:
                random.shuffle(possible_inner_coords)
                common_portal_coords = possible_inner_coords[:num_common_portal_coords]

        for floor_id in range(self.num_floors):
            builder = SingleFloorBuilder(self.width, self.height)
            self.world_maps[floor_id] = builder.world_map
            self.floor_details.append({"id": floor_id, "map": self.world_maps[floor_id]})

        self._ensure_portal_connectivity(common_portal_coords)

    def _ensure_portal_connectivity(
        self, common_portal_coords: List[tuple[int, int]]
    ):
        if self.num_floors <= 1 or not common_portal_coords:
            return

        taken_portal_coords_globally: set[tuple[int, int]] = set()
        parent = list(range(self.num_floors))

        def find_set(i):
            if parent[i] == i:
                return i
            parent[i] = find_set(parent[i])
            return parent[i]

        def unite_sets(i, j):
            r_i, r_j = find_set(i), find_set(j)
            if r_i != r_j:
                parent[r_i] = r_j
                return True
            return False

        available_common_coords = list(common_portal_coords)
        random.shuffle(available_common_coords)

        for i in range(self.num_floors):
            f1_id, f2_id = i, (i + 1) % self.num_floors
            if find_set(f1_id) == find_set(f2_id) and self.num_floors > 2:
                continue
            if not available_common_coords:
                break
            p_x, p_y = available_common_coords.pop(0)
            t1 = self.world_maps[f1_id].get_tile(p_x, p_y)
            t2 = self.world_maps[f2_id].get_tile(p_x, p_y)
            if t1 and t2:
                t1.type, t1.is_portal, t1.portal_to_floor_id = "portal", True, f2_id
                t2.type, t2.is_portal, t2.portal_to_floor_id = "portal", True, f1_id
                unite_sets(f1_id, f2_id)
                taken_portal_coords_globally.add((p_x, p_y))
            else:
                available_common_coords.append((p_x, p_y))

        num_c = sum(1 for i in range(self.num_floors) if parent[i] == i)
        attempts = 0
        max_attempts = self.num_floors * 2
        while num_c > 1 and attempts < max_attempts:
            attempts += 1
            if not available_common_coords:
                break
            roots = [r for r in range(self.num_floors) if parent[r] == r]
            if len(roots) < 2:
                break
            r1c, r2c = random.sample(roots, 2)
            comp1_f = [fid for fid in range(self.num_floors) if find_set(fid) == r1c]
            comp2_f = [fid for fid in range(self.num_floors) if find_set(fid) == r2c]
            if not comp1_f or not comp2_f:
                continue
            f1l, f2l = random.choice(comp1_f), random.choice(comp2_f)
            if not available_common_coords:
                break
            px2, py2 = available_common_coords.pop(0)
            t1n, t2n = (
                self.world_maps[f1l].get_tile(px2, py2),
                self.world_maps[f2l].get_tile(px2, py2),
            )
            if t1n and t2n:
                t1n.type, t1n.is_portal, t1n.portal_to_floor_id = "portal", True, f2l
                t2n.type, t2n.is_portal, t2n.portal_to_floor_id = "portal", True, f1l
                unite_sets(f1l, f2l)
                taken_portal_coords_globally.add((px2, py2))
                num_c = sum(
                    1 for i_comp in range(self.num_floors) if parent[i_comp] == i_comp
                )
            else:
                available_common_coords.append((px2, py2))
        if sum(1 for i_loop in range(self.num_floors) if parent[i_loop] == i_loop) > 1:
            print("Warning: WG could not connect all floors using common coords.")

    def _place_amulet_of_yendor(
        self, player_start_floor: int
    ) -> Tuple[int, int, int]:
        amulet_floor_id = player_start_floor
        if self.num_floors > 1:
            possible_amulet_floors = [
                f["id"] for f in self.floor_details if f["id"] != player_start_floor
            ]
            amulet_floor_id = (
                random.choice(possible_amulet_floors)
                if possible_amulet_floors
                else (player_start_floor + 1) % self.num_floors
            )

        amulet_map = self.world_maps[amulet_floor_id]
        amulet_floor_tiles = [
            (x, y)
            for x in range(1, self.width - 1)
            for y in range(1, self.height - 1)
            if amulet_map.get_tile(x, y) and amulet_map.get_tile(x, y).type == "floor"
        ]

        if not amulet_floor_tiles:
            # Fallback: place amulet on player's start floor if amulet floor is solid rock
            amulet_floor_id = player_start_floor
            amulet_map = self.world_maps[amulet_floor_id]
            amulet_floor_tiles = [
                (x, y)
                for x in range(1, self.width - 1)
                for y in range(1, self.height - 1)
                if amulet_map.get_tile(x, y)
                and amulet_map.get_tile(x, y).type == "floor"
            ]
            if not amulet_floor_tiles:
                # If player's floor is also solid, place it somewhere, anywhere
                amulet_map.set_tile_type(
                    self.width // 2, self.height // 2, "floor"
                )
                amulet_floor_tiles.append((self.width // 2, self.height // 2))

        amulet_pos = random.choice(amulet_floor_tiles)
        amulet_item = Item("Amulet of Yendor", "Object of quest!", {"type": "quest"})
        amulet_map.place_item(amulet_item, amulet_pos[0], amulet_pos[1])

        return amulet_pos[0], amulet_pos[1], amulet_floor_id

    def build(
        self,
    ) -> Tuple[
        dict[int, WorldMap],
        Tuple[int, int, int],
        Tuple[int, int, int],
        List[dict],
    ]:
        self._initialize_world()

        for floor_id in range(self.num_floors):
            single_floor_seed = (
                random.randint(0, 2**32 - 1) if self.seed is not None else None
            )
            builder = SingleFloorBuilder(
                self.width,
                self.height,
                seed=single_floor_seed,
                existing_map=self.world_maps[floor_id],
            )
            world_map, floor_start_pos, floor_poi_pos = builder.build()
            self.world_maps[floor_id] = world_map
            for fd_item in self.floor_details:
                if fd_item["id"] == floor_id:
                    fd_item["start"] = floor_start_pos
                    fd_item["poi"] = floor_poi_pos
                    break

        player_start_floor = 0
        player_start_detail = next(
            (fd for fd in self.floor_details if fd["id"] == player_start_floor), None
        )
        if not player_start_detail or "start" not in player_start_detail:
            px, py = (self.width // 2, self.height // 2)
        else:
            px, py = player_start_detail["start"]
        player_start_full_pos = (px, py, player_start_floor)

        amulet_full_pos = self._place_amulet_of_yendor(player_start_floor)

        return (
            self.world_maps,
            player_start_full_pos,
            amulet_full_pos,
            self.floor_details,
        )

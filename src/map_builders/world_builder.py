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
            self.floor_details.append(
                {"id": floor_id, "map": self.world_maps[floor_id]}
            )

        self._ensure_portal_connectivity(common_portal_coords)

    def _ensure_portal_connectivity(self, common_portal_coords: List[tuple[int, int]]):
        if self.num_floors <= 1 or not common_portal_coords:
            return

        portal_coords_per_floor: dict[int, set[tuple[int, int]]] = {
            i: set() for i in range(self.num_floors)
        }
        parent = list(range(self.num_floors))

        def find_set(i):
            if parent[i] == i:
                return i
            parent[i] = find_set(parent[i])
            return parent[i]

        def unite_sets(i, j):
            i_id, j_id = find_set(i), find_set(j)
            if i_id != j_id:
                parent[i_id] = j_id
                return True
            return False

        shuffled_coords = list(common_portal_coords)
        random.shuffle(shuffled_coords)

        # Create a ring of portals
        for i in range(self.num_floors):
            f1_id, f2_id = i, (i + 1) % self.num_floors
            if find_set(f1_id) == find_set(f2_id) and self.num_floors > 2:
                continue

            coord_found = False
            for p_x, p_y in shuffled_coords:
                if (p_x, p_y) not in portal_coords_per_floor[f1_id] and (
                    p_x,
                    p_y,
                ) not in portal_coords_per_floor[f2_id]:
                    t1 = self.world_maps[f1_id].get_tile(p_x, p_y)
                    t2 = self.world_maps[f2_id].get_tile(p_x, p_y)
                    if t1 and t2:
                        t1.type, t1.is_portal, t1.portal_to_floor_id = (
                            "portal",
                            True,
                            f2_id,
                        )
                        t2.type, t2.is_portal, t2.portal_to_floor_id = (
                            "portal",
                            True,
                            f1_id,
                        )
                        portal_coords_per_floor[f1_id].add((p_x, p_y))
                        portal_coords_per_floor[f2_id].add((p_x, p_y))
                        unite_sets(f1_id, f2_id)
                        coord_found = True
                        break
            if not coord_found:
                print(
                    f"Warning: Could not find a unique portal location for {f1_id}-{f2_id}"
                )

        # Ensure full connectivity
        num_components = sum(1 for i in range(self.num_floors) if parent[i] == i)
        while num_components > 1:
            roots = [i for i in range(self.num_floors) if parent[i] == i]
            if len(roots) < 2:
                break
            r1_root, r2_root = random.sample(roots, 2)
            comp1_floors = [i for i in range(self.num_floors) if find_set(i) == r1_root]
            comp2_floors = [i for i in range(self.num_floors) if find_set(i) == r2_root]
            if not comp1_floors or not comp2_floors:
                continue
            f1_rand, f2_rand = random.choice(comp1_floors), random.choice(comp2_floors)

            coord_found_for_extra_link = False
            for p_x, p_y in shuffled_coords:
                if (p_x, p_y) not in portal_coords_per_floor[f1_rand] and (
                    p_x,
                    p_y,
                ) not in portal_coords_per_floor[f2_rand]:
                    t1 = self.world_maps[f1_rand].get_tile(p_x, p_y)
                    t2 = self.world_maps[f2_rand].get_tile(p_x, p_y)
                    if t1 and t2:
                        t1.type, t1.is_portal, t1.portal_to_floor_id = (
                            "portal",
                            True,
                            f2_rand,
                        )
                        t2.type, t2.is_portal, t2.portal_to_floor_id = (
                            "portal",
                            True,
                            f1_rand,
                        )
                        portal_coords_per_floor[f1_rand].add((p_x, p_y))
                        portal_coords_per_floor[f2_rand].add((p_x, p_y))
                        unite_sets(f1_rand, f2_rand)
                        num_components = sum(
                            1 for i in range(self.num_floors) if parent[i] == i
                        )
                        coord_found_for_extra_link = True
                        break
            if not coord_found_for_extra_link:
                print("Warning: Could not connect all map components.")
                break

    def _place_amulet_of_yendor(self, player_start_floor: int) -> Tuple[int, int, int]:
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
                amulet_map.set_tile_type(self.width // 2, self.height // 2, "floor")
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

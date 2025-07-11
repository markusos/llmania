import unittest

# from src.player import Player # Removed as unused (F401) - this was from ruff output, not my current manual list
from src.map_algorithms.pathfinding import PathFinder
from src.monster import Monster
from src.tile import Tile
from src.world_map import WorldMap


class TestPathFinderMultiFloor(unittest.TestCase):
    def setUp(self):
        self.path_finder = PathFinder()
        self.world_maps: dict[int, WorldMap] = {}

    def _create_floor(
        self, floor_id: int, width: int, height: int, layout: list[str]
    ) -> WorldMap:
        world_map = WorldMap(width, height)
        for r, row_str in enumerate(layout):
            for c, char in enumerate(row_str):
                tile_type = "wall"
                item = None
                monster = None
                portal_to_floor_id = None

                if char == ".":
                    tile_type = "floor"
                elif char == "#":
                    tile_type = "wall"
                elif char == "S":
                    tile_type = "floor"
                elif char == "G":
                    tile_type = "floor"
                elif char == "M":
                    tile_type = "floor"
                    monster = Monster(
                        name="TestMonster", health=10, attack_power=2, x=c, y=r
                    )
                elif char.isdigit():
                    tile_type = "portal"
                    portal_to_floor_id = int(char)

                tile = Tile(
                    tile_type=tile_type,
                    monster=monster,
                    item=item,
                    portal_to_floor_id=portal_to_floor_id,
                )
                if tile_type == "portal":
                    tile.is_portal = True

                world_map.grid[r][c] = tile
                world_map.grid[r][c].is_explored = True
        return world_map

    def test_path_on_single_floor_simple(self):
        layout_floor0_actual = ["S.G"]
        self.world_maps[0] = self._create_floor(0, 3, 1, layout_floor0_actual)

        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(2, 0),
            goal_floor_id=0,
        )
        self.assertIsNotNone(path)
        expected_path = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        if path:
            self.assertEqual(path, expected_path)

    def test_path_on_single_floor_obstacles(self):
        layout_floor0_actual = ["S.#", ".#.", "..G"]
        self.world_maps[0] = self._create_floor(0, 3, 3, layout_floor0_actual)

        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(2, 2),
            goal_floor_id=0,
        )
        self.assertIsNotNone(path)
        expected_path = [(0, 0, 0), (0, 1, 0), (0, 2, 0), (1, 2, 0), (2, 2, 0)]
        if path:
            self.assertEqual(path, expected_path)

    def test_no_path_on_single_floor(self):
        layout_floor0_actual = ["S#G", "###", "..."]
        self.world_maps[0] = self._create_floor(0, 3, 3, layout_floor0_actual)
        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(2, 0),
            goal_floor_id=0,
        )
        self.assertIsNone(path)

    def test_path_through_portal(self):
        self.world_maps.clear()
        # Unused layout variables were here, removed for F841
        layout_f0_actual = ["S.1"]
        layout_f1_actual = ["G.0"]

        self.world_maps[0] = self._create_floor(0, 3, 1, layout_f0_actual)
        self.world_maps[1] = self._create_floor(1, 3, 1, layout_f1_actual)

        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(0, 0),
            goal_floor_id=1,
        )
        self.assertIsNotNone(path)
        expected_path = [
            (0, 0, 0),
            (1, 0, 0),
            (2, 0, 0),
            (2, 0, 1),
            (1, 0, 1),
            (0, 0, 1),
        ]
        if path:
            self.assertEqual(path, expected_path)

    def test_path_blocked_by_monster_not_goal(self):
        layout_floor0_actual = ["S.M.G"]
        self.world_maps[0] = self._create_floor(0, 5, 1, layout_floor0_actual)
        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(4, 0),
            goal_floor_id=0,
        )
        self.assertIsNone(
            path, "Path should be blocked by monster if monster is not the goal."
        )

    def test_path_to_monster_is_goal(self):
        layout_floor0_actual = ["S.M"]
        self.world_maps[0] = self._create_floor(0, 3, 1, layout_floor0_actual)
        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(2, 0),
            goal_floor_id=0,
        )
        self.assertIsNotNone(path)
        expected_path = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        if path:
            self.assertEqual(path, expected_path)

    def test_portal_to_wall_is_not_used(self):
        layout_f0_actual = ["S.1"]
        layout_f1_actual = ["G.#"]

        self.world_maps[0] = self._create_floor(0, 3, 1, layout_f0_actual)
        self.world_maps[1] = self._create_floor(1, 3, 1, layout_f1_actual)

        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(0, 0),
            goal_floor_id=1,
        )
        self.assertIsNone(
            path, "Pathfinder should not use a portal leading into a wall."
        )

    def test_path_multiple_portals_optimal(self):
        layout_f0_v2_actual = ["S.1...1"]
        layout_f1_v2_actual = ["..0.G.0"]

        self.world_maps.clear()
        self.world_maps[0] = self._create_floor(0, 7, 1, layout_f0_v2_actual)
        self.world_maps[1] = self._create_floor(1, 7, 1, layout_f1_v2_actual)

        path = self.path_finder.find_path_bfs(
            world_maps=self.world_maps,
            start_pos_xy=(0, 0),
            start_floor_id=0,
            goal_pos_xy=(4, 0),
            goal_floor_id=1,
        )
        self.assertIsNotNone(path)
        expected_optimal_path = [
            (0, 0, 0),
            (1, 0, 0),
            (2, 0, 0),
            (2, 0, 1),
            (3, 0, 1),
            (4, 0, 1),
        ]
        if path:
            self.assertEqual(path, expected_optimal_path)


if __name__ == "__main__":
    unittest.main()

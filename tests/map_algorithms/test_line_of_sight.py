"""Tests for line of sight algorithms."""

import unittest

from src.map_algorithms.line_of_sight import (
    calculate_visible_tiles,
    get_line_tiles,
    has_clear_line_of_sight,
)
from src.world_map import WorldMap


class TestGetLineTiles(unittest.TestCase):
    """Tests for Bresenham line algorithm."""

    def test_horizontal_line(self):
        """Test a horizontal line from (0,0) to (5,0)."""
        tiles = get_line_tiles(0, 0, 5, 0)
        expected = [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]
        self.assertEqual(tiles, expected)

    def test_vertical_line(self):
        """Test a vertical line from (0,0) to (0,5)."""
        tiles = get_line_tiles(0, 0, 0, 5)
        expected = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5)]
        self.assertEqual(tiles, expected)

    def test_diagonal_line(self):
        """Test a diagonal line from (0,0) to (3,3)."""
        tiles = get_line_tiles(0, 0, 3, 3)
        # Should include tiles along the diagonal
        self.assertEqual(len(tiles), 3)
        self.assertIn((3, 3), tiles)

    def test_same_point(self):
        """Test when start and end are the same point."""
        tiles = get_line_tiles(5, 5, 5, 5)
        self.assertEqual(tiles, [])

    def test_negative_direction(self):
        """Test a line going in negative direction."""
        tiles = get_line_tiles(5, 5, 2, 5)
        expected = [(4, 5), (3, 5), (2, 5)]
        self.assertEqual(tiles, expected)


class TestHasClearLineOfSight(unittest.TestCase):
    """Tests for line of sight blocking."""

    def setUp(self):
        """Create a simple test map."""
        self.world_map = WorldMap(width=10, height=10)

    def test_clear_line_of_sight(self):
        """Test LOS with no walls in the way."""
        # All tiles are floor by default
        result = has_clear_line_of_sight(self.world_map, 1, 1, 5, 1)
        self.assertTrue(result)

    def test_blocked_by_wall(self):
        """Test LOS blocked by a wall."""
        self.world_map.set_tile_type(3, 1, "wall")
        result = has_clear_line_of_sight(self.world_map, 1, 1, 5, 1)
        self.assertFalse(result)

    def test_wall_at_destination_not_blocking(self):
        """Wall at the destination should not block LOS to that tile."""
        self.world_map.set_tile_type(5, 1, "wall")
        result = has_clear_line_of_sight(self.world_map, 1, 1, 5, 1)
        self.assertTrue(result)

    def test_adjacent_tiles(self):
        """Adjacent tiles should always have clear LOS."""
        result = has_clear_line_of_sight(self.world_map, 5, 5, 5, 6)
        self.assertTrue(result)

    def test_diagonal_blocked(self):
        """Test diagonal LOS blocked by wall."""
        self.world_map.set_tile_type(3, 3, "wall")
        result = has_clear_line_of_sight(self.world_map, 1, 1, 5, 5)
        self.assertFalse(result)


class TestCalculateVisibleTiles(unittest.TestCase):
    """Tests for visible tile calculation."""

    def setUp(self):
        """Create a simple test map."""
        self.world_map = WorldMap(width=20, height=20)

    def test_origin_always_visible(self):
        """The origin tile should always be visible."""
        visible = calculate_visible_tiles(self.world_map, 10, 10, 5)
        self.assertIn((10, 10), visible)

    def test_adjacent_tiles_visible(self):
        """Adjacent tiles should be visible."""
        visible = calculate_visible_tiles(self.world_map, 10, 10, 5)
        self.assertIn((11, 10), visible)
        self.assertIn((10, 11), visible)
        self.assertIn((9, 10), visible)
        self.assertIn((10, 9), visible)

    def test_respects_view_radius(self):
        """Tiles beyond view radius should not be visible."""
        visible = calculate_visible_tiles(self.world_map, 10, 10, 3)
        # Tile at distance 5 should not be visible with radius 3
        self.assertNotIn((15, 10), visible)

    def test_wall_blocks_visibility(self):
        """Walls should block visibility of tiles behind them."""
        # Create a wall
        self.world_map.set_tile_type(12, 10, "wall")
        visible = calculate_visible_tiles(self.world_map, 10, 10, 5)

        # Wall itself should be visible
        self.assertIn((12, 10), visible)

        # Tiles directly behind the wall should not be visible
        self.assertNotIn((13, 10), visible)
        self.assertNotIn((14, 10), visible)

    def test_can_see_around_corners(self):
        """Test that tiles around walls are visible."""
        self.world_map.set_tile_type(12, 10, "wall")
        visible = calculate_visible_tiles(self.world_map, 10, 10, 5)

        # Tiles above and below the wall should still be visible
        self.assertIn((12, 9), visible)
        self.assertIn((12, 11), visible)


if __name__ == "__main__":
    unittest.main()

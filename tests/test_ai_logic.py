"""Tests for AILogic core functionality."""

import random
import unittest
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

from src.ai_logic.main import AILogic
from src.items import Item
from src.message_log import MessageLog
from src.monster import Monster
from src.player import Player
from src.tile import Tile
from src.world_map import WorldMap


class TestAILogic(unittest.TestCase):
    """Test suite for AILogic core functionality."""

    def setUp(self):
        self.mock_player = MagicMock(spec=Player)
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.current_floor_id = 0
        self.mock_player.health = 100
        self.mock_player.max_health = 100
        self.mock_player.inventory = MagicMock()
        self.mock_player.inventory.items = []  # No items in inventory
        # Mock combat stats for should_engage_monster
        self.mock_player.get_attack_power.return_value = 5
        self.mock_player.get_defense.return_value = 0
        self.mock_player.equipment = MagicMock()
        self.mock_player.equipment.slots = {}

        self.ai_visible_maps: Dict[int, WorldMap] = {0: WorldMap(10, 10)}

        self.message_log = MagicMock(spec=MessageLog)

        with (
            patch("src.ai_logic.main.TargetFinder") as self.mock_target_finder,
            patch("src.ai_logic.main.Explorer") as self.mock_explorer,
        ):
            self.ai = AILogic(
                player=self.mock_player,
                ai_visible_maps=self.ai_visible_maps,
                message_log=self.message_log,
                random_generator=random.Random(),
            )
            self.ai.target_finder.find_health_potions.return_value = []

    def _create_floor_layout(
        self,
        floor_id: int,
        width: int,
        height: int,
        layout: list[str],
        is_ai_map: bool = True,
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
                        "TestMonster",
                        10,
                        2,
                        random.Random(),
                        x=c,
                        y=r,
                    )
                elif char.isdigit():
                    tile_type = "portal"
                    portal_to_floor_id = int(char)
                elif char == "R":
                    tile_type = "floor"
                    item = Item(name="Rock", description="A plain rock", properties={})

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

        if is_ai_map:
            self.ai_visible_maps[floor_id] = world_map
        return world_map

    def _setup_tile_at(
        self,
        floor_id: int,
        x: int,
        y: int,
        item=None,
        monster=None,
        explored=True,
        tile_type="floor",
        portal_to: Optional[int] = None,
    ):
        if floor_id not in self.ai_visible_maps:
            self.ai_visible_maps[floor_id] = WorldMap(10, 10)

        target_map = self.ai_visible_maps[floor_id]
        tile = target_map.get_tile(x, y)
        if not tile:
            tile = Tile()
            target_map.grid[y][x] = tile

        if tile:
            tile.item = item
        tile.monster = monster
        tile.type = tile_type
        tile.is_explored = explored
        tile.is_portal = portal_to is not None
        tile.portal_to_floor_id = portal_to

        return tile

    def test_ai_picks_up_item_on_tile(self):
        """Test AI chooses to pick up item when standing on one."""
        self.mock_player.current_floor_id = 0
        sword_item = MagicMock(spec=Item)
        sword_item.name = "Sword"
        sword_item.properties = {}
        self._setup_tile_at(0, self.mock_player.x, self.mock_player.y, item=sword_item)

        action = self.ai.get_next_action()
        # Utility AI should return a take command for the item
        self.assertIsNotNone(action)
        self.assertEqual(action[0], "take")

    def test_ai_attacks_adjacent_monster(self):
        """Test AI chooses to attack when monster is adjacent."""
        self.mock_player.current_floor_id = 0
        monster_mock = Monster(
            "Goblin",
            10,
            3,
            random.Random(),
            x=self.mock_player.x + 1,
            y=self.mock_player.y,
        )
        self._setup_tile_at(
            0, self.mock_player.x + 1, self.mock_player.y, monster=monster_mock
        )

        action = self.ai.get_next_action()
        # Utility AI should return an attack command
        self.assertIsNotNone(action)
        self.assertEqual(action[0], "attack")

    def test_ai_explores_when_no_other_targets(self):
        """Test AI explores when no items or monsters nearby."""
        self.ai.target_finder.find_quest_items.return_value = []
        self.ai.target_finder.find_health_potions.return_value = []
        self.ai.target_finder.find_other_items.return_value = []
        self.ai.target_finder.find_monsters.return_value = []
        self.ai.explorer.find_unvisited_portals.return_value = []
        self.ai.explorer.find_portal_to_unexplored_floor.return_value = []
        self.ai.explorer.find_exploration_targets.return_value = [
            (1, 2, 0),
            (1, 1, 0),
        ]

        action = self.ai.get_next_action()
        # AI should return a move command to explore
        self.assertIsNotNone(action)
        # Should have set a path for exploration
        self.assertIsNotNone(self.ai.current_path)

    def test_ai_breaks_out_of_stuck_loop(self):
        """Test AI breaks out when stuck in oscillation loop."""
        self.ai.player_pos_history = [(1, 1), (1, 2), (1, 1), (1, 2)]
        self.ai.current_path = [(1, 3, 0)]
        self.ai.explorer.find_exploration_targets.return_value = None

        self.ai.get_next_action()

        # Path should be cleared when loop detected
        self.assertIsNone(self.ai.current_path)

    def test_calculate_survival_threshold_base(self):
        """Test base survival threshold is 0.5 when player has healing items."""
        self.mock_player.health = 100
        self.mock_player.max_health = 100
        # Mock that player has healing items
        with patch.object(self.ai.player_view, "has_item_type", return_value=True):
            threshold = self.ai.calculate_survival_threshold()
            self.assertEqual(threshold, 0.5)

    def test_calculate_survival_threshold_no_healing(self):
        """Test survival threshold increases when no healing available."""
        self.mock_player.health = 100
        self.mock_player.max_health = 100
        self.mock_player.inventory.items = []

        # Ensure has_item_type returns False
        with patch.object(self.ai.player_view, "has_item_type", return_value=False):
            threshold = self.ai.calculate_survival_threshold()
            # Base 0.5 + 0.15 for no healing = 0.65
            self.assertEqual(threshold, 0.65)

    def test_is_cornered_returns_true_when_surrounded(self):
        """Test is_cornered returns True when all exits blocked."""
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.current_floor_id = 0

        # Create a map where player is surrounded by walls
        self._create_floor_layout(
            0, 5, 5, ["#####", "#P###", "#####", "#####", "#####"]
        )

        is_cornered = self.ai._is_cornered()
        self.assertTrue(is_cornered)

    def test_is_cornered_returns_false_when_has_exits(self):
        """Test is_cornered returns False when exits available."""
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.current_floor_id = 0

        # Create a map where player has exits
        self._create_floor_layout(
            0, 5, 5, ["#####", "#P..#", "#...#", "#...#", "#####"]
        )

        is_cornered = self.ai._is_cornered()
        self.assertFalse(is_cornered)


if __name__ == "__main__":
    unittest.main()

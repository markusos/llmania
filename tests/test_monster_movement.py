import random
import unittest
from unittest.mock import MagicMock

from src.game_engine import GameEngine
from src.monster import Monster
from src.world_map import WorldMap


class TestFastMonsterMovement(unittest.TestCase):
    def setUp(self):
        self.world_map = WorldMap(width=10, height=10)
        self.game_engine = GameEngine(
            debug_mode=True,
            seed=12345,
            world_maps={0: self.world_map},
            player_start_pos=(5, 5, 0),
        )
        self.player = self.game_engine.player
        self.random_generator = random.Random(12345)

    def test_fast_monster_moves_based_on_speed(self):
        # Monster with speed 10, should move every turn
        monster_fast = Monster(
            "Fast",
            10,
            1,
            self.random_generator,
            x=1,
            y=1,
            move_speed=10,
        )
        self.world_map.place_monster(monster_fast, 1, 1)
        monster_fast.ai = MagicMock()
        monster_fast.ai.get_next_action.return_value = ("move", "south")

        # Initial positions
        self.assertEqual(monster_fast.y, 1)

        # Turn 1
        self.game_engine.game_manager._handle_monster_actions()
        self.assertEqual(monster_fast.y, 2)  # Fast monster moves


class TestSlowMonsterMovement(unittest.TestCase):
    def setUp(self):
        self.world_map = WorldMap(width=10, height=10)
        self.game_engine = GameEngine(
            debug_mode=True,
            seed=12345,
            world_maps={0: self.world_map},
            player_start_pos=(5, 5, 0),
        )
        self.player = self.game_engine.player
        self.random_generator = random.Random(12345)

    def test_slow_monster_moves_based_on_speed(self):
        # Monster with speed 1, should move every 10 turns
        monster_slow = Monster(
            "Slow",
            10,
            1,
            self.random_generator,
            x=2,
            y=2,
            move_speed=1,
        )
        self.world_map.place_monster(monster_slow, 2, 2)
        monster_slow.ai = MagicMock()
        monster_slow.ai.get_next_action.return_value = ("move", "north")

        # Initial positions
        self.assertEqual(monster_slow.y, 2)

        # Turns 1-9
        for _ in range(9):
            self.game_engine.game_manager._handle_monster_actions()
            self.assertEqual(monster_slow.y, 2)  # Slow monster does not move

        # Turn 10
        self.game_engine.game_manager._handle_monster_actions()
        self.assertEqual(monster_slow.y, 1)  # Slow monster moves


if __name__ == "__main__":
    unittest.main()

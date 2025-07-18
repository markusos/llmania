import unittest
from unittest.mock import MagicMock

from src.game_engine import GameEngine
from src.monster import Monster
from src.player import Player
from src.world_map import WorldMap


class TestMonsterMovement(unittest.TestCase):
    def setUp(self):
        self.game_engine = GameEngine(debug_mode=True)
        self.player = self.game_engine.player
        self.world_map = self.game_engine.world_maps[self.player.current_floor_id]

    def test_monster_moves_based_on_speed(self):
        # Monster with speed 10, should move every turn
        monster_fast = Monster(name="Fast", health=10, attack_power=1, x=1, y=1, move_speed=10)
        self.world_map.place_monster(monster_fast, 1, 1)
        monster_fast.ai = MagicMock()
        monster_fast.ai.get_next_action.return_value = ("move", "south")

        # Monster with speed 1, should move every 10 turns
        monster_slow = Monster(name="Slow", health=10, attack_power=1, x=2, y=2, move_speed=1)
        self.world_map.place_monster(monster_slow, 2, 2)
        monster_slow.ai = MagicMock()
        monster_slow.ai.get_next_action.return_value = ("move", "north")

        # Initial positions
        self.assertEqual(monster_fast.y, 1)
        self.assertEqual(monster_slow.y, 2)

        # Turn 1
        self.game_engine._handle_monster_actions()
        self.assertEqual(monster_fast.y, 2)  # Fast monster moves
        self.assertEqual(monster_slow.y, 2)  # Slow monster does not move

        # Turns 2-9
        for _ in range(8):
            self.game_engine._handle_monster_actions()
            self.assertEqual(monster_slow.y, 2) # Slow monster does not move

        # Turn 10
        self.game_engine._handle_monster_actions()
        self.assertEqual(monster_slow.y, 1) # Slow monster moves

if __name__ == "__main__":
    unittest.main()

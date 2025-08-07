import unittest
from unittest.mock import MagicMock

from src.commands.inventory_command import InventoryCommand
from src.game_engine import GameEngine
from src.player import Player
from src.world_map import WorldMap


class TestInventoryCommand(unittest.TestCase):
    def setUp(self):
        self.player = Player(x=1, y=1, current_floor_id=0, health=10)
        self.world_map = WorldMap(width=10, height=10)
        self.message_log = MagicMock()
        self.game_engine = MagicMock(spec=GameEngine)
        self.game_engine.renderer = MagicMock()
        self.game_engine.command_buffer = ""

    def test_execute_toggles_inventory_mode_on(self):
        self.game_engine.input_mode = "normal"
        cmd = InventoryCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=(0, 0, 0),
            game_engine=self.game_engine,
        )
        cmd.execute()
        self.assertEqual(self.game_engine.input_mode, "inventory")

    def test_execute_toggles_inventory_mode_off(self):
        self.game_engine.input_mode = "inventory"
        cmd = InventoryCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=(0, 0, 0),
            game_engine=self.game_engine,
        )
        cmd.execute()
        self.assertEqual(self.game_engine.input_mode, "normal")
        self.assertTrue(self.game_engine.renderer.render_all.called)


if __name__ == "__main__":
    unittest.main()

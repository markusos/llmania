import unittest
from unittest.mock import MagicMock, patch

from src.game_engine import GameEngine
from src.item import Item


class TestGameEngineItems(unittest.TestCase):
    def setUp(self):
        with patch("src.game_engine.WorldGenerator") as mock_world_gen:
            mock_map = MagicMock()
            mock_map.width = 20
            mock_map.height = 10
            mock_map.get_tile.return_value.type = "floor"
            mock_world_gen.return_value.generate_world.return_value = (
                {0: mock_map},
                (1, 1, 0),
                (5, 5, 0),
                [],
            )
            self.game_engine = GameEngine(debug_mode=True)

    def test_teleport_player(self):
        scroll = Item("Teleport Scroll", "Teleports you.", {"type": "teleport"})
        self.game_engine.player.take_item(scroll)
        self.game_engine._handle_item_use(scroll)
        self.assertNotEqual(
            (self.game_engine.player.x, self.game_engine.player.y), (1, 1)
        )

    def test_handle_invisibility(self):
        self.game_engine.player.invisibility_turns = 1
        self.game_engine._handle_invisibility()
        self.assertEqual(self.game_engine.player.invisibility_turns, 0)


if __name__ == "__main__":
    unittest.main()

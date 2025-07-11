import unittest
from unittest.mock import MagicMock

from src.commands.move_command import MoveCommand
from src.item import Item  # Added Item import
from src.message_log import MessageLog
from src.player import Player
from src.tile import Tile
from src.world_map import WorldMap


class TestMoveCommand(unittest.TestCase):
    def setUp(self):
        self.player = Player(x=1, y=1, current_floor_id=0, health=10)
        self.message_log = MagicMock(spec=MessageLog)

        # Default single floor for most tests
        self.world_map_f0 = WorldMap(width=3, height=3)
        for r in range(3):
            for c in range(3):
                self.world_map_f0.grid[r][c] = Tile(tile_type="floor")

        self.world_maps = {0: self.world_map_f0}

        # Default winning position (not relevant for all move tests)
        self.winning_position = (2, 2, 0)

    def test_move_north_success(self):
        self.player.x, self.player.y = 1, 1
        move_cmd = MoveCommand(
            player=self.player,
            world_map=self.world_maps[0],  # Current floor's map
            message_log=self.message_log,
            winning_position=self.winning_position,
            argument="north",
            world_maps=self.world_maps,
        )
        result = move_cmd.execute()
        self.assertEqual(self.player.y, 0)
        self.assertEqual(self.player.x, 1)
        self.message_log.add_message.assert_called_with("You move north.")
        self.assertFalse(result.get("game_over", False))

    def test_move_to_wall(self):
        self.player.x, self.player.y = 0, 0
        self.world_maps[0].grid[0][1] = Tile(tile_type="wall")  # Wall to the east

        move_cmd = MoveCommand(
            player=self.player,
            world_map=self.world_maps[0],
            message_log=self.message_log,
            winning_position=self.winning_position,
            argument="east",
            world_maps=self.world_maps,
        )
        result = move_cmd.execute()
        self.assertEqual(self.player.x, 0)  # Position should not change
        self.assertEqual(self.player.y, 0)
        self.message_log.add_message.assert_called_with("You can't move there.")
        self.assertFalse(result.get("game_over", False))

    def test_move_into_monster(self):
        self.player.x, self.player.y = 0, 0
        monster_tile = Tile(tile_type="floor")
        monster_mock = MagicMock()  # Simple mock for monster
        monster_mock.name = "Goblin"
        monster_tile.monster = monster_mock
        self.world_maps[0].grid[0][1] = monster_tile  # Monster at (1,0)

        move_cmd = MoveCommand(
            player=self.player,
            world_map=self.world_maps[0],
            message_log=self.message_log,
            winning_position=self.winning_position,
            argument="east",  # Moving towards (1,0)
            world_maps=self.world_maps,
        )
        result = move_cmd.execute()
        self.assertEqual(self.player.x, 0)  # Position should not change
        self.assertEqual(self.player.y, 0)
        self.message_log.add_message.assert_called_with("You bump into a Goblin!")
        self.assertFalse(result.get("game_over", False))

    def test_move_through_portal(self):
        self.player.x, self.player.y = 0, 0
        self.player.current_floor_id = 0

        # Setup floor 0
        portal_tile_f0 = Tile(tile_type="portal", portal_to_floor_id=1)
        self.world_maps[0].grid[0][1] = (
            portal_tile_f0  # Portal at (1,0) on floor 0 to floor 1
        )

        # Setup floor 1 (not strictly needed for MoveCommand logic, but good practice)
        world_map_f1 = WorldMap(width=3, height=3)
        for r in range(3):
            for c in range(3):
                world_map_f1.grid[r][c] = Tile(tile_type="floor")
        portal_tile_f1 = Tile(tile_type="portal", portal_to_floor_id=0)
        world_map_f1.grid[0][1] = (
            portal_tile_f1  # Corresponding portal at (1,0) on floor 1 to floor 0
        )
        self.world_maps[1] = world_map_f1

        move_cmd = MoveCommand(
            player=self.player,
            world_map=self.world_maps[0],  # Player is on floor 0
            message_log=self.message_log,
            winning_position=self.winning_position,  # Assume win pos is not here
            argument="east",  # Moving towards portal at (1,0)
            world_maps=self.world_maps,  # Pass all maps
            game_engine=None,  # Not needed for this specific test path
        )
        result = move_cmd.execute()

        self.assertEqual(self.player.x, 1, "Player should be at portal X coord")
        self.assertEqual(self.player.y, 0, "Player should be at portal Y coord")
        self.assertEqual(self.player.current_floor_id, 1, "Player should be on floor 1")
        self.message_log.add_message.assert_called_with(
            "You step through the portal to floor 1!"
        )
        self.assertFalse(result.get("game_over", False))

    def test_move_to_winning_position_on_correct_floor(self):
        self.player.x, self.player.y = 1, 2
        self.player.current_floor_id = 0

        # Winning position is (2,2,0)
        self.winning_position = (2, 2, 0)
        # Place a quest item at the winning position on floor 0
        win_tile = self.world_maps[0].get_tile(2, 2)
        if win_tile:
            win_tile.item = Item("Amulet", "Quest item", {"type": "quest"})

        move_cmd = MoveCommand(
            player=self.player,
            world_map=self.world_maps[0],
            message_log=self.message_log,
            winning_position=self.winning_position,
            argument="east",  # Moves player from (1,2) to (2,2)
            world_maps=self.world_maps,
        )
        result = move_cmd.execute()
        self.assertEqual(self.player.x, 2)
        self.assertEqual(self.player.y, 2)
        self.assertEqual(self.player.current_floor_id, 0)
        self.message_log.add_message.assert_any_call("You move east.")
        self.message_log.add_message.assert_any_call(
            "You reached the Amulet of Yendor's location!"
        )
        self.assertFalse(
            result.get("game_over", False)
        )  # Game over not set by move, but by take.


if __name__ == "__main__":
    unittest.main()

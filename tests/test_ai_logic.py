import unittest
from unittest.mock import (
    MagicMock,
    patch,
)  # Import call for checking multiple calls if needed

# Assuming these are the correct paths to your classes
from ai_logic import AILogic
from item import Item  # Actual class for spec
from message_log import MessageLog  # Import MessageLog
from monster import Monster  # Actual class for spec
from player import Player  # Actual class for spec
from tile import Tile  # Actual class for spec
from world_map import WorldMap  # Actual class for spec


class TestAILogic(unittest.TestCase):
    def setUp(self):
        self.mock_player = MagicMock(spec=Player)
        self.mock_world_map = MagicMock(spec=WorldMap)
        self.message_log = MagicMock(spec=MessageLog)  # Mock MessageLog

        # Initialize AILogic with mocked dependencies
        self.ai = AILogic(
            player=self.mock_player,
            world_map=self.mock_world_map,
            message_log=self.message_log,
        )

        # Default player attributes
        self.mock_player.x = 1  # Using (1,1) as a common starting point in a grid
        self.mock_player.y = 1
        self.mock_player.health = 20
        # Mock inventory as a dictionary {item_name: item_mock}
        self.mock_player.inventory = {}

        # Default current tile setup
        self.current_tile_mock = MagicMock(spec=Tile)
        self.current_tile_mock.item = None
        self.current_tile_mock.monster = None

        # Default setup for get_tile: (player_x, player_y) returns current_tile_mock
        # Other coordinates will return a new default tile mock by default in tests
        # unless specified otherwise.
        self.mock_world_map.get_tile.return_value = self.current_tile_mock

        # Default for is_valid_move (can be overridden in specific tests)
        self.mock_world_map.is_valid_move.return_value = True

        # Reset visited tiles for each test
        self.ai.visited_tiles = []
        self.ai.last_move_command = None

    def _setup_tile_at(self, x, y, item=None, monster=None):
        """Helper to mock a specific tile at given coordinates."""
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = item
        tile_mock.monster = monster

        # This lambda allows get_tile to return specific mocks for specific coordinates
        def side_effect_get_tile(tile_x, tile_y):
            if tile_x == self.mock_player.x and tile_y == self.mock_player.y:
                return self.current_tile_mock
            if tile_x == x and tile_y == y:
                return tile_mock
            # Default for other tiles: empty, no monster, no item
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            return empty_tile

        self.mock_world_map.get_tile.side_effect = side_effect_get_tile
        return tile_mock

    def test_ai_takes_quest_item(self):
        quest_item = MagicMock(spec=Item)
        quest_item.name = "Amulet of Yendor"
        quest_item.properties = {"type": "quest"}

        self.current_tile_mock.item = quest_item
        # get_tile already defaults to current_tile_mock for player pos

        action = self.ai.get_next_action()
        self.assertEqual(action, ("take", "Amulet of Yendor"))
        self.message_log.add_message.assert_any_call(
            "AI: Found quest item Amulet of Yendor!"
        )

    def test_ai_uses_health_potion_when_low_health(self):
        self.mock_player.health = 5  # Low health

        health_potion_mock = MagicMock(spec=Item)
        health_potion_mock.name = "Health Potion"
        health_potion_mock.quantity = 1
        self.mock_player.inventory = {"Health Potion": health_potion_mock}

        action = self.ai.get_next_action()
        self.assertEqual(action, ("use", "Health Potion"))
        self.message_log.add_message.assert_any_call(
            "AI: Low health, using Health Potion."
        )

    def test_ai_does_not_use_health_potion_if_not_present(self):
        self.mock_player.health = 5
        self.mock_player.inventory = {}  # No potions

        # To ensure it doesn't try to use, we need to check what it does instead
        # Assuming it would look around or explore if no other pressing actions
        self.mock_world_map.is_valid_move.return_value = False  # Make it look
        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        # Check that "AI: Low health..." was NOT called
        for call_args in self.message_log.add_message.call_args_list:
            self.assertNotIn("AI: Low health, using Health Potion.", call_args[0][0])

    def test_ai_takes_regular_item_when_health_ok_and_no_quest_item(self):
        self.mock_player.health = 20  # Health OK

        sword_item = MagicMock(spec=Item)
        sword_item.name = "Sword"
        sword_item.properties = {}  # Not a quest item

        self.current_tile_mock.item = sword_item
        # self.mock_world_map.get_tile.return_value = self.current_tile_mock

        action = self.ai.get_next_action()
        self.assertEqual(action, ("take", "Sword"))
        self.message_log.add_message.assert_any_call("AI: Found item Sword, taking it.")

    def test_ai_attacks_adjacent_monster(self):
        self.mock_player.health = 20
        self.current_tile_mock.item = None  # No items on current tile

        monster_mock = MagicMock(spec=Monster)
        monster_mock.name = "Goblin"

        # Place monster to the east (player at 1,1 -> monster at 2,1)
        self._setup_tile_at(
            self.mock_player.x + 1, self.mock_player.y, monster=monster_mock
        )
        self.mock_world_map.is_valid_move.side_effect = lambda x, y: not (
            x == self.mock_player.x + 1 and y == self.mock_player.y
        )

        action = self.ai.get_next_action()
        self.assertEqual(action, ("attack", "Goblin"))
        self.message_log.add_message.assert_any_call("AI: Attacking Goblin.")

    def test_ai_attacks_one_of_multiple_adjacent_monsters(self):
        monster1_mock = MagicMock(spec=Monster)
        monster1_mock.name = "Orc"
        monster2_mock = MagicMock(spec=Monster)
        monster2_mock.name = "Slime"

        # Monster to the North (1,0) and East (2,1) of player (1,1)
        north_tile = self._setup_tile_at(
            self.mock_player.x, self.mock_player.y - 1, monster=monster1_mock
        )
        east_tile = self._setup_tile_at(
            self.mock_player.x + 1, self.mock_player.y, monster=monster2_mock
        )

        # Ensure get_tile returns the correct tiles when checking adjacency
        def side_effect_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            if x == self.mock_player.x and y == self.mock_player.y - 1:
                return north_tile  # North
            if x == self.mock_player.x + 1 and y == self.mock_player.y:
                return east_tile  # East
            # Other adjacent tiles are empty
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            return empty_tile

        self.mock_world_map.get_tile.side_effect = side_effect_get_tile

        action = self.ai.get_next_action()
        # AI picks first one found (N, S, W, E order in _get_adjacent_monsters).
        self.assertEqual(action, ("attack", "Orc"))
        self.message_log.add_message.assert_any_call("AI: Attacking Orc.")

    @patch("random.choice")
    def test_ai_explores_unvisited_tile(self, mock_random_choice):
        # Player at (1,1). North (1,0) is unvisited. East (2,1) is visited.
        self.ai.visited_tiles.append(
            (self.mock_player.x + 1, self.mock_player.y)
        )  # Visited East

        # Define behavior for get_tile and is_valid_move
        # Player is at (1,1)
        # Tile North (1,0) is valid and unvisited.
        # Tile East (2,1) is valid but visited.
        # Other tiles (S, W) could be valid/invalid, but North preferred.

        empty_tile_north = MagicMock(spec=Tile)
        empty_tile_north.item = None
        empty_tile_north.monster = None
        empty_tile_east = MagicMock(spec=Tile)
        empty_tile_east.item = None
        empty_tile_east.monster = None

        def side_effect_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            if x == self.mock_player.x and y == self.mock_player.y - 1:
                return empty_tile_north  # North
            if x == self.mock_player.x + 1 and y == self.mock_player.y:
                return empty_tile_east  # East
            # For simplicity, make other directions invalid for this test
            return None

        self.mock_world_map.get_tile.side_effect = side_effect_get_tile

        def side_effect_is_valid_move(x, y):
            if x == self.mock_player.x and y == self.mock_player.y - 1:
                return True  # North is valid
            if x == self.mock_player.x + 1 and y == self.mock_player.y:
                return True  # East is valid
            return False  # Other directions invalid

        self.mock_world_map.is_valid_move.side_effect = side_effect_is_valid_move

        # random.choice will be called with a list of unvisited valid moves.
        # In this setup, only moving North leads to an unvisited tile.
        mock_random_choice.return_value = ("move", "north")

        action = self.ai.get_next_action()

        self.assertEqual(action, ("move", "north"))
        # random.choice called with list containing only the unvisited option.
        mock_random_choice.assert_called_once_with([("move", "north")])
        self.message_log.add_message.assert_any_call(
            "AI: Exploring unvisited. Moving north."
        )
        self.assertIn(
            (self.mock_player.x, self.mock_player.y), self.ai.visited_tiles
        )  # Current tile marked visited

    @patch("random.choice")
    def test_ai_explores_randomly_when_all_neighbors_visited(self, mock_random_choice):
        # Player at (1,1). All adjacent N,S,E,W are valid but visited.
        self.ai.visited_tiles.append(
            (self.mock_player.x, self.mock_player.y)
        )  # Current
        self.ai.visited_tiles.append(
            (self.mock_player.x, self.mock_player.y - 1)
        )  # North
        self.ai.visited_tiles.append(
            (self.mock_player.x, self.mock_player.y + 1)
        )  # South
        self.ai.visited_tiles.append(
            (self.mock_player.x - 1, self.mock_player.y)
        )  # West
        self.ai.visited_tiles.append(
            (self.mock_player.x + 1, self.mock_player.y)
        )  # East

        # All adjacent tiles are empty and valid
        def side_effect_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            return empty_tile

        self.mock_world_map.get_tile.side_effect = side_effect_get_tile
        self.mock_world_map.is_valid_move.return_value = True  # All directions valid

        # AI should pick a random valid move from all possible moves.
        # Don't care about avoiding back-and-forth for this test, just that it moves.
        mock_random_choice.return_value = ("move", "east")

        action = self.ai.get_next_action()

        self.assertEqual(action, ("move", "east"))
        # random.choice is called with all valid moves: N, S, W, E
        expected_choices = [
            ("move", "north"),
            ("move", "south"),
            ("move", "west"),
            ("move", "east"),
        ]

        # The actual call to random.choice might have these in a different order
        # So, check that the list of args to random.choice contains the same elements
        args, _ = mock_random_choice.call_args
        self.assertCountEqual(
            args[0], expected_choices
        )  # Checks for same elements, regardless of order
        self.message_log.add_message.assert_any_call(
            "AI: All visited nearby. Moving east."
        )

    def test_ai_looks_when_stuck(self):
        # Player at (1,1), surrounded by walls (no valid moves)
        self.mock_world_map.is_valid_move.return_value = False  # All moves are invalid

        # get_tile returns None for adjacent if is_valid_move is false in AILogic.
        # Good practice to ensure they are not special.
        def side_effect_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            return None  # Or a wall tile if your map has specific wall tiles

        self.mock_world_map.get_tile.side_effect = side_effect_get_tile

        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        self.message_log.add_message.assert_any_call(
            "AI: No valid moves, looking around."
        )
        self.assertEqual(self.ai.last_move_command, ("look", None))


if __name__ == "__main__":
    unittest.main()

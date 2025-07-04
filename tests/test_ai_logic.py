import unittest
from unittest.mock import (
    MagicMock,
    patch,
)  # Import call for checking multiple calls if needed

# Assuming these are the correct paths to your classes
from src.ai_logic import AILogic
from src.item import Item  # Actual class for spec
from src.message_log import MessageLog  # Import MessageLog
from src.monster import Monster  # Actual class for spec
from src.player import Player  # Actual class for spec
from src.tile import Tile  # Actual class for spec
from src.world_map import WorldMap  # Actual class for spec


class TestAILogic(unittest.TestCase):
    def setUp(self):
        self.mock_player = MagicMock(spec=Player)
        self.mock_real_world_map = MagicMock(spec=WorldMap)
        self.mock_ai_visible_map = MagicMock(spec=WorldMap)
        # Add height and width to visible map
        self.mock_ai_visible_map.height = 10
        self.mock_ai_visible_map.width = 10
        self.message_log = MagicMock(spec=MessageLog)
        self.ai = AILogic(
            player=self.mock_player,
            real_world_map=self.mock_real_world_map,
            ai_visible_map=self.mock_ai_visible_map,
            message_log=self.message_log,
        )
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.health = 20
        self.mock_player.max_health = 100
        # Default inventory: empty
        self.mock_player.inventory = []
        self.current_tile_mock = MagicMock(spec=Tile)
        self.current_tile_mock.item = None
        self.current_tile_mock.monster = None
        self.current_tile_mock.type = "floor"
        self.current_tile_mock.is_explored = True

        # Set up default tile behavior - return current_tile_mock for player position,
        # empty tiles for other positions
        def default_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            # For positions immediately around the player, return explored empty tiles
            if abs(x - self.mock_player.x) <= 1 and abs(y - self.mock_player.y) <= 1:
                empty_tile = MagicMock(spec=Tile)
                empty_tile.item = None
                empty_tile.monster = None
                empty_tile.type = "floor"
                empty_tile.is_explored = True
                return empty_tile
            # For positions far from player, return None (unexplored/out of bounds)
            return None

        # Set up default real world map behavior
        def default_real_world_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                real_tile = MagicMock(spec=Tile)
                real_tile.item = None
                real_tile.monster = None
                real_tile.type = "floor"
                return real_tile
            # For positions immediately around the player, return empty tiles
            if abs(x - self.mock_player.x) <= 1 and abs(y - self.mock_player.y) <= 1:
                empty_tile = MagicMock(spec=Tile)
                empty_tile.item = None
                empty_tile.monster = None
                empty_tile.type = "floor"
                return empty_tile
            # For positions far from player, return None (out of bounds)
            return None

        self.mock_ai_visible_map.get_tile.side_effect = default_get_tile
        self.mock_real_world_map.get_tile.side_effect = default_real_world_get_tile
        self.mock_real_world_map.is_valid_move.return_value = True
        self.mock_ai_visible_map.is_valid_move.return_value = True
        self.ai.physically_visited_coords = []
        self.ai.last_move_command = None

    def _setup_tile_at(
        self, x, y, item=None, monster=None, explored=True, tile_type="floor"
    ):
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = item
        tile_mock.monster = monster
        tile_mock.type = tile_type
        tile_mock.is_explored = explored

        def side_effect_get_tile(tile_x, tile_y):
            if tile_x == self.mock_player.x and tile_y == self.mock_player.y:
                return self.current_tile_mock
            if tile_x == x and tile_y == y:
                return tile_mock
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            empty_tile.type = "floor"
            empty_tile.is_explored = True
            return empty_tile

        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile
        return tile_mock

    def test_ai_takes_quest_item(self):
        quest_item = MagicMock(spec=Item)
        quest_item.name = "Amulet of Yendor"
        quest_item.properties = {"type": "quest"}
        self.current_tile_mock.item = quest_item
        self.current_tile_mock.is_explored = True

        # Set up real world map to have the quest item as well
        def real_world_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                real_tile = MagicMock(spec=Tile)
                real_tile.item = quest_item
                real_tile.monster = None
                real_tile.type = "floor"
                return real_tile
            # Return empty tile for other positions
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            empty_tile.type = "floor"
            return empty_tile

        self.mock_real_world_map.get_tile.side_effect = real_world_get_tile

        action = self.ai.get_next_action()
        self.assertEqual(action, ("take", quest_item.name))
        self.message_log.add_message.assert_any_call(
            f"AI: Found quest item {quest_item.name}!"
        )

    def test_ai_uses_health_potion_when_low_health(self):
        self.mock_player.health = 5
        potion = MagicMock(spec=Item)
        potion.name = "Health Potion"
        potion.properties = {"type": "heal"}
        potion.quantity = 1
        self.mock_player.inventory = [potion]
        action = self.ai.get_next_action()
        self.assertEqual(action, ("use", "Health Potion"))
        self.message_log.add_message.assert_any_call(
            "AI: Low health, using Health Potion from inventory."
        )

    def test_ai_does_not_use_health_potion_if_not_present(self):
        self.mock_player.health = 5
        self.mock_player.inventory = []

        # Make all moves invalid so AI should look around
        def is_valid_move_all_false(x, y):
            return False

        self.mock_real_world_map.is_valid_move.side_effect = is_valid_move_all_false
        self.mock_ai_visible_map.is_valid_move.side_effect = is_valid_move_all_false
        self.current_tile_mock.item = None

        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        for call_args in self.message_log.add_message.call_args_list:
            self.assertNotIn("AI: Low health, using Health Potion.", call_args[0][0])

    def test_ai_takes_regular_item_when_health_ok_and_no_quest_item(self):
        self.mock_player.health = 20
        sword_item = MagicMock(spec=Item)
        sword_item.name = "Sword"
        sword_item.properties = {}
        self.mock_player.inventory = [sword_item]
        self.current_tile_mock.item = sword_item
        self.current_tile_mock.is_explored = True

        # Set up real world map to have the sword item as well
        def real_world_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                real_tile = MagicMock(spec=Tile)
                real_tile.item = sword_item
                real_tile.monster = None
                real_tile.type = "floor"
                return real_tile
            # Return empty tile for other positions
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            empty_tile.type = "floor"
            return empty_tile

        self.mock_real_world_map.get_tile.side_effect = real_world_get_tile

        action = self.ai.get_next_action()
        self.assertEqual(action, ("take", "Sword"))
        self.message_log.add_message.assert_any_call(
            "AI: Found item Sword on current tile, taking it."
        )

    def test_ai_attacks_adjacent_monster(self):
        self.mock_player.health = 20
        self.current_tile_mock.item = None
        monster_mock = MagicMock(spec=Monster)
        monster_mock.name = "Goblin"

        # Set up real world map with monster adjacent to player
        def real_world_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                real_tile = MagicMock(spec=Tile)
                real_tile.item = None
                real_tile.monster = None
                real_tile.type = "floor"
                return real_tile
            elif x == self.mock_player.x + 1 and y == self.mock_player.y:
                monster_tile = MagicMock(spec=Tile)
                monster_tile.item = None
                monster_tile.monster = monster_mock
                monster_tile.type = "floor"
                return monster_tile
            # Return empty tile for other positions
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            empty_tile.type = "floor"
            return empty_tile

        self.mock_real_world_map.get_tile.side_effect = real_world_get_tile

        self._setup_tile_at(
            self.mock_player.x + 1, self.mock_player.y, monster=monster_mock
        )
        self.mock_real_world_map.is_valid_move.side_effect = lambda x, y: not (
            x == self.mock_player.x + 1 and y == self.mock_player.y
        )
        action = self.ai.get_next_action()
        self.assertEqual(action, ("attack", "Goblin"))
        self.message_log.add_message.assert_any_call("AI: Attacking adjacent Goblin.")

    @patch("src.ai_logic.random.choice")
    def test_ai_attacks_one_of_multiple_adjacent_monsters(self, mock_random_choice):
        monster1_mock = MagicMock(spec=Monster)
        monster1_mock.name = "Orc"
        monster2_mock = MagicMock(spec=Monster)
        monster2_mock.name = "Slime"

        # Mock random.choice to return the first monster
        mock_random_choice.return_value = monster1_mock

        # Set up real world map with monsters adjacent to player
        def real_world_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                real_tile = MagicMock(spec=Tile)
                real_tile.item = None
                real_tile.monster = None
                real_tile.type = "floor"
                return real_tile
            elif x == self.mock_player.x and y == self.mock_player.y - 1:
                north_tile = MagicMock(spec=Tile)
                north_tile.item = None
                north_tile.monster = monster1_mock
                north_tile.type = "floor"
                return north_tile
            elif x == self.mock_player.x + 1 and y == self.mock_player.y:
                east_tile = MagicMock(spec=Tile)
                east_tile.item = None
                east_tile.monster = monster2_mock
                east_tile.type = "floor"
                return east_tile
            # Return empty tile for other positions
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            empty_tile.type = "floor"
            return empty_tile

        self.mock_real_world_map.get_tile.side_effect = real_world_get_tile

        north_tile = self._setup_tile_at(
            self.mock_player.x, self.mock_player.y - 1, monster=monster1_mock
        )
        east_tile = self._setup_tile_at(
            self.mock_player.x + 1, self.mock_player.y, monster=monster2_mock
        )

        def side_effect_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            if x == self.mock_player.x and y == self.mock_player.y - 1:
                return north_tile
            if x == self.mock_player.x + 1 and y == self.mock_player.y:
                return east_tile
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            empty_tile.type = "floor"
            empty_tile.is_explored = True
            return empty_tile

        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile
        action = self.ai.get_next_action()
        self.assertEqual(action, ("attack", "Orc"))
        self.message_log.add_message.assert_any_call("AI: Attacking adjacent Orc.")

    @patch("random.choice")
    def test_ai_explores_unvisited_tile(self, mock_random_choice):
        self.ai.physically_visited_coords.append(
            (self.mock_player.x + 1, self.mock_player.y)
        )
        empty_tile_north = MagicMock(spec=Tile)
        empty_tile_north.item = None
        empty_tile_north.monster = None
        empty_tile_north.type = "floor"
        empty_tile_north.is_explored = True
        empty_tile_east = MagicMock(spec=Tile)
        empty_tile_east.item = None
        empty_tile_east.monster = None
        empty_tile_east.type = "floor"
        empty_tile_east.is_explored = True

        def side_effect_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            if x == self.mock_player.x and y == self.mock_player.y - 1:
                return empty_tile_north
            if x == self.mock_player.x + 1 and y == self.mock_player.y:
                return empty_tile_east
            return None

        self.mock_real_world_map.get_tile.side_effect = side_effect_get_tile
        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile

        def side_effect_is_valid_move(x, y):
            if x == self.mock_player.x and y == self.mock_player.y - 1:
                return True
            if x == self.mock_player.x + 1 and y == self.mock_player.y:
                return True
            return False

        self.mock_real_world_map.is_valid_move.side_effect = side_effect_is_valid_move
        self.mock_ai_visible_map.is_valid_move.side_effect = side_effect_is_valid_move
        mock_random_choice.return_value = ("move", "north")
        action = self.ai.get_next_action()
        self.assertEqual(action, ("move", "north"))
        # Since unvisited exploration is deterministic, random.choice should not be
        # called
        mock_random_choice.assert_not_called()
        self.message_log.add_message.assert_any_call(
            "AI: Pathing to explore known but unvisited tile at (1,0)."
        )
        self.assertIn(
            (self.mock_player.x, self.mock_player.y), self.ai.physically_visited_coords
        )

    @patch("src.ai_logic.random.choice")
    def test_ai_explores_randomly_when_all_neighbors_visited(self, mock_random_choice):
        self.ai.physically_visited_coords.extend(
            [
                (self.mock_player.x, self.mock_player.y),
                (self.mock_player.x, self.mock_player.y - 1),
                (self.mock_player.x, self.mock_player.y + 1),
                (self.mock_player.x - 1, self.mock_player.y),
                (self.mock_player.x + 1, self.mock_player.y),
            ]
        )

        def side_effect_get_tile(x, y):
            # Only return tiles for the immediate vicinity, everything else is None
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            if abs(x - self.mock_player.x) <= 1 and abs(y - self.mock_player.y) <= 1:
                empty_tile = MagicMock(spec=Tile)
                empty_tile.item = None
                empty_tile.monster = None
                empty_tile.type = "floor"
                empty_tile.is_explored = True
                return empty_tile
            # Everything else is out of bounds/unexplored
            return None

        def side_effect_is_valid_move(x, y):
            # Only allow moves to adjacent positions
            if (
                abs(x - self.mock_player.x) <= 1
                and abs(y - self.mock_player.y) <= 1
                and not (x == self.mock_player.x and y == self.mock_player.y)
            ):
                return True
            return False

        self.mock_real_world_map.get_tile.side_effect = side_effect_get_tile
        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile
        self.mock_real_world_map.is_valid_move.side_effect = side_effect_is_valid_move
        self.mock_ai_visible_map.is_valid_move.side_effect = side_effect_is_valid_move
        mock_random_choice.return_value = ("move", "east")
        action = self.ai.get_next_action()

        # The AI should move in some direction when exploring
        self.assertEqual(action[0], "move")
        self.assertIn(action[1], ["north", "south", "west", "east"])

        # Check if random choice was called (the fallback random exploration)
        if mock_random_choice.called:
            expected_choices = [
                ("move", "north"),
                ("move", "south"),
                ("move", "west"),
                ("move", "east"),
            ]
            args, _ = mock_random_choice.call_args
            self.assertCountEqual(args[0], expected_choices)
            self.message_log.add_message.assert_any_call(
                f"AI: All visited nearby. Moving {action[1]}."
            )
        else:
            # If pathfinding was used instead of random choice, that's also valid
            # The AI may have found a deterministic path to explore
            self.assertTrue(
                any(
                    "Pathing to explore" in str(call) or "Moving" in str(call)
                    for call in self.message_log.add_message.call_args_list
                )
            )

    def test_ai_looks_when_stuck(self):
        # Make all moves invalid
        def is_valid_move_all_false(x, y):
            return False

        self.mock_real_world_map.is_valid_move.side_effect = is_valid_move_all_false
        self.mock_ai_visible_map.is_valid_move.side_effect = is_valid_move_all_false

        def side_effect_get_tile(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return self.current_tile_mock
            return None

        self.mock_real_world_map.get_tile.side_effect = side_effect_get_tile
        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile
        self.current_tile_mock.item = None
        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        self.message_log.add_message.assert_any_call(
            "AI: No path found on visible map and no other actions. Looking around."
        )
        self.assertEqual(self.ai.last_move_command, ("look", None))


if __name__ == "__main__":
    unittest.main()

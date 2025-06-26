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
        self.mock_world_map = MagicMock(spec=WorldMap)
        self.message_log = MagicMock(spec=MessageLog)  # Mock MessageLog

        # Initialize AILogic with mocked dependencies
        # For AILogic, we need a "real" map (for checking actual tiles)
        # and an "ai_visible_map" (for AI's decisions and pathfinding).
        # In tests, these can often be the same mock if not testing fog of war directly,
        # or different if testing how AI reacts to limited visibility.
        self.mock_real_world_map = MagicMock(spec=WorldMap)
        self.mock_ai_visible_map = MagicMock(spec=WorldMap) # This is what AI uses

        self.ai = AILogic(
            player=self.mock_player,
            real_world_map=self.mock_real_world_map, # For AILogic to update its vision
            ai_visible_map=self.mock_ai_visible_map, # For AILogic to make decisions
            message_log=self.message_log,
        )

        # Default player attributes
        self.mock_player.x = 1  # Using (1,1) as a common starting point in a grid
        self.mock_player.y = 1
        self.mock_player.health = 20
        # Mock inventory as a dictionary {item_name: item_mock}
        self.mock_player.inventory = {}

        # Default current tile setup (on the AI's visible map)
        self.current_tile_mock = MagicMock(spec=Tile)
        self.current_tile_mock.item = None
        self.current_tile_mock.monster = None
        self.current_tile_mock.is_explored = True # Assume current tile is explored

        # Default setup for get_tile on the AI's visible map:
        # (player_x, player_y) returns current_tile_mock
        self.mock_ai_visible_map.get_tile.return_value = self.current_tile_mock
        # Also, ensure real map has some defaults if update_visibility is ever called directly in a test
        self.mock_real_world_map.get_tile.return_value = MagicMock(spec=Tile, is_explored=False)


        # Default for is_valid_move (used by some older tests, pathfinder uses walkable tiles)
        # This should ideally check the ai_visible_map.
        self.mock_ai_visible_map.is_valid_move = MagicMock(return_value=True)
        # PathFinder will use ai_visible_map.get_tile(x,y).type != "wall" etc.

        # Reset AI state for each test
        self.ai.physically_visited_coords = [] # Updated attribute name
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
            # Default for other tiles: empty, no monster, no item, but explored
            empty_tile = MagicMock(spec=Tile)
            empty_tile.item = None
            empty_tile.monster = None
            empty_tile.is_explored = True # Assume AI can see these default tiles if pathing
            return empty_tile

        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile
        # Ensure the real map also provides some kind of tile for update_visibility
        self.mock_real_world_map.get_tile.side_effect = side_effect_get_tile
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

        # To ensure it doesn't try to use, we need to check what it does instead.
        # AI will try to find a path. If no path/target, it looks.
        # Make pathfinding return no path.
        with patch.object(self.ai.path_finder, 'find_path_bfs', return_value=None):
            action = self.ai.get_next_action()
            self.assertEqual(action, ("look", None)) # Should look if no path and no other action

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
            self.mock_player.x + 1, self.mock_player.y, monster=monster_mock
        )
        # Ensure the tile is marked explored for the AI to see the monster
        tile_with_monster = self.mock_ai_visible_map.get_tile(self.mock_player.x + 1, self.mock_player.y)
        if tile_with_monster: # Should exist due to _setup_tile_at
            tile_with_monster.is_explored = True

        action = self.ai.get_next_action()
        self.assertEqual(action, ("attack", "Goblin"))
        self.message_log.add_message.assert_any_call("AI: Attacking Goblin.")

    def test_ai_attacks_one_of_multiple_adjacent_monsters(self):
        monster1_mock = MagicMock(spec=Monster)
        monster1_mock.name = "Orc"
        monster2_mock = MagicMock(spec=Monster)
        monster2_mock.name = "Slime"

        # Monster to the North (1,0) and East (2,1) of player (1,1)
        north_tile = self._setup_tile_at(self.mock_player.x, self.mock_player.y - 1, monster=monster1_mock)
        north_tile.is_explored = True # Make visible to AI
        east_tile = self._setup_tile_at(self.mock_player.x + 1, self.mock_player.y, monster=monster2_mock)
        east_tile.is_explored = True # Make visible to AI


        # The _setup_tile_at already configures mock_ai_visible_map.get_tile's side_effect.
        # We just need to ensure the tiles are marked as explored.

        action = self.ai.get_next_action()
        # AI decision logic for choosing which monster to attack if multiple are adjacent
        # depends on the implementation of _get_adjacent_monsters and random.choice.
        # The current _get_adjacent_monsters returns a list, and AI attacks a random choice.
        # For testing, we can mock random.choice if specific behavior is needed,
        # or accept any valid attack. Here, we check if it attacks one of them.
        # Based on current AILogic, _get_adjacent_monsters checks N,S,W,E.
        # So Orc (North) should be found first if random choice is not a factor.
        # However, AILogic uses random.choice(adjacent_monsters).
        # Let's assert it's one of them.
        self.assertIn(action[0], ["attack"])
        self.assertIn(action[1], ["Orc", "Slime"])

        # To make the test deterministic for the message, we can patch random.choice
        with patch('random.choice', return_value=monster1_mock): # Force choosing Orc
            action = self.ai.get_next_action()
            self.assertEqual(action, ("attack", "Orc"))
            self.message_log.add_message.assert_any_call("AI: Attacking Orc.")

    @patch("random.choice") # This test was already patching random.choice
    def test_ai_explores_unvisited_tile(self, mock_random_choice):
        # Player at (1,1). North (1,0) is unvisited (is_explored=False).
        # East (2,1) is visited (is_explored=True, type='floor').
        # AI should try to path to an explored tile adjacent to an unexplored one,
        # or to an unvisited but known floor tile.

        # Current player tile (1,1)
        self.current_tile_mock.type = "floor"
        self.current_tile_mock.is_explored = True
        self.ai.physically_visited_coords.append((1,1))


        # Tile North (1,0) - target for exploration edge, itself unexplored
        tile_north_unexplored = MagicMock(spec=Tile)
        tile_north_unexplored.type = "floor" # Real type
        tile_north_unexplored.is_explored = False # Fog for AI

        # Tile East (2,1) - explored, physically visited
        tile_east_explored_visited = MagicMock(spec=Tile)
        tile_east_explored_visited.type = "floor"
        tile_east_explored_visited.is_explored = True
        self.ai.physically_visited_coords.append((2,1))

        # Tile South (1,2) - explored, walkable, but NOT physically visited by player yet
        tile_south_explored_unvisited = MagicMock(spec=Tile)
        tile_south_explored_unvisited.type = "floor"
        tile_south_explored_unvisited.is_explored = True
        # (1,2) is not in self.ai.physically_visited_coords initially for this part

        def side_effect_get_ai_visible_map(x, y):
            if x == 1 and y == 1: return self.current_tile_mock
            if x == 1 and y == 0: return tile_north_unexplored # Unseen by AI
            if x == 2 and y == 1: return tile_east_explored_visited # Seen, visited
            if x == 1 and y == 2: return tile_south_explored_unvisited # Seen, not physically visited
            # Other tiles can be default explored floor for pathfinding simplicity
            default_tile = MagicMock(spec=Tile, type="floor", is_explored=True)
            default_tile.monster = None
            default_tile.item = None
            return default_tile

        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_ai_visible_map
        self.mock_ai_visible_map.width = 5
        self.mock_ai_visible_map.height = 5


        # PathFinder will be used. AI prioritizes:
        # 1. Quest items (none here)
        # 2. Other items (none here)
        # 3. Monsters (none here)
        # 4. Explore unvisited but REVEALED Floor Tiles (tile_south_explored_unvisited at (1,2))
        # 5. Explore towards edges of current visibility (e.g. move to (1,1) to see (1,0)) -
        #    Path to (1,1) is not useful. Path to (player_x, player_y-1) i.e. (1,0) is not possible as it's unexplored.
        #    It will path to an explored tile ADJACENT to an unexplored one. Player is at (1,1), (1,0) is unexplored.
        #    So (1,1) is adjacent to unexplored (1,0). Path to (1,1) is trivial.
        #    The AI should choose to move to (1,2) - the unvisited known floor tile.

        # Patch PathFinder to control path result for this specific scenario
        # Expect path to (1,2)
        with patch.object(self.ai.path_finder, 'find_path_bfs', return_value=[(1,1), (1,2)]) as mock_find_path:
            action = self.ai.get_next_action()
            # Expected: move south to (1,2)
            self.assertEqual(action, ("move", "south"))
            mock_find_path.assert_called_with(self.mock_ai_visible_map, (1,1), (1,2))
            # The message log will reflect pathing to this "unvisited known tile"
            # self.message_log.add_message.assert_any_call(
            #     "AI: Pathing to explore known but unvisited tile at (1,2)." # Message format might change
            # )

        self.assertIn((1,1), self.ai.physically_visited_coords)


    @patch("random.choice") # This test was already patching random.choice
    def test_ai_explores_randomly_when_all_neighbors_visited(self, mock_random_choice):
        # Player at (1,1). All adjacent N,S,E,W are valid, explored, and physically visited.
        # AI should look around as per current advanced logic if no other targets.
        # The old test expected a random move. The new logic is more complex.
        # If all known tiles are physically visited, and no items/monsters,
        # it tries to path to an edge of fog. If map fully explored, it might look.

        self.mock_player.x, self.mock_player.y = 1, 1
        self.current_tile_mock.type = "floor"
        self.current_tile_mock.is_explored = True

        self.ai.physically_visited_coords = [(1,1), (1,0), (1,2), (0,1), (2,1)] # All neighbors visited

        # All adjacent tiles are empty, explored, and floor type
        def side_effect_get_tile(x, y):
            tile = MagicMock(spec=Tile)
            tile.type = "floor"
            tile.is_explored = True
            tile.monster = None
            tile.item = None
            if (x,y) == (self.mock_player.x, self.mock_player.y):
                return self.current_tile_mock
            return tile

        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile
        self.mock_ai_visible_map.width = 3
        self.mock_ai_visible_map.height = 3
        # This setup implies a 3x3 map fully explored and visited.

        # In this scenario (fully explored small map, no items/monsters), AI should look.
        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        self.message_log.add_message.assert_any_call(
            "AI: No path found on visible map and no other actions. Looking around."
        )


    def test_ai_looks_when_stuck(self):
        # Player at (1,1), surrounded by walls on the AI's visible map.
        self.mock_player.x, self.mock_player.y = 1, 1
        self.current_tile_mock.type = "floor" # Player's current tile is floor
        self.current_tile_mock.is_explored = True

        def side_effect_get_tile(x, y):
            if x == 1 and y == 1:
                return self.current_tile_mock
            # All adjacent tiles are walls and explored
            wall_tile = MagicMock(spec=Tile)
            wall_tile.type = "wall"
            wall_tile.is_explored = True
            wall_tile.monster = None
            wall_tile.item = None
            return wall_tile

        self.mock_ai_visible_map.get_tile.side_effect = side_effect_get_tile
        self.mock_ai_visible_map.width = 3
        self.mock_ai_visible_map.height = 3
        # PathFinder will find no path to any floor tile other than current.

        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        self.message_log.add_message.assert_any_call(
            "AI: No path found on visible map and no other actions. Looking around." # Updated message
        )
        self.assertEqual(self.ai.last_move_command, ("look", None))


if __name__ == "__main__":
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

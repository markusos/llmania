import unittest
from unittest.mock import MagicMock

from src.command_processor import CommandProcessor
from src.item import Item
from src.message_log import MessageLog
from src.monster import Monster
from src.player import Player
from src.tile import Tile
from src.world_map import WorldMap


class TestCommandProcessor(unittest.TestCase):
    def setUp(self):
        self.command_processor = CommandProcessor()
        self.mock_player = MagicMock(spec=Player)
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.health = 100
        self.mock_player.inventory = []
        self.mock_player.equipped_weapon = None

        self.mock_world_map = MagicMock(spec=WorldMap)
        self.mock_world_map.get_tile = MagicMock()
        self.mock_world_map.is_valid_move = MagicMock(return_value=True)
        self.mock_world_map.remove_item = MagicMock()
        self.mock_world_map.place_item = MagicMock()
        self.mock_world_map.remove_monster = MagicMock()

        # For multi-floor, CommandProcessor needs a dictionary of world_maps
        self.mock_world_maps_dict = {0: self.mock_world_map}  # Player starts on floor 0

        self.message_log = MagicMock(spec=MessageLog)
        self.win_pos = (10, 10, 0)  # Now a 3-tuple (x,y,floor_id)

        self.mock_game_engine = MagicMock()  # For the game_engine argument

    def common_process_command(self, command_tuple):
        # Reset mocks for player's position before each command if necessary,
        # or ensure tests set it up as needed. For now, it's static.
        # Player's current_floor_id is assumed to be 0 by default in setUp for mock_player
        if not hasattr(self.mock_player, "current_floor_id"):  # Ensure it's set
            self.mock_player.current_floor_id = 0

        return self.command_processor.process_command(
            command_tuple,
            self.mock_player,
            self.mock_world_maps_dict,  # Pass the dictionary of maps
            self.message_log,
            self.win_pos,
            game_engine=self.mock_game_engine,  # Pass the mock game_engine
        )

    # test_get_adjacent_monsters removed (logic in Command/AttackCommand)

    def test_process_command_move_valid(self):
        # Ensure player position is reset for this test or set as needed.
        # self.mock_player.x = 1
        # self.mock_player.y = 1
        tile_mock = MagicMock(spec=Tile)
        tile_mock.monster = None
        tile_mock.is_portal = False  # Added for MoveCommand check
        tile_mock.portal_to_floor_id = None  # Added for MoveCommand check
        self.mock_world_map.get_tile.return_value = tile_mock
        result = self.common_process_command(("move", "north"))
        self.mock_player.move.assert_called_once_with(0, -1)
        self.message_log.add_message.assert_any_call("You move north.")
        self.assertFalse(result["game_over"])

    def test_process_command_move_invalid_wall(self):
        self.mock_world_map.is_valid_move.return_value = False
        result = self.common_process_command(("move", "east"))
        self.mock_player.move.assert_not_called()
        self.message_log.add_message.assert_any_call("You can't move there.")
        self.assertFalse(result["game_over"])

    def test_process_command_move_into_monster(self):
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Goblin"
        tile_mock = MagicMock(spec=Tile)
        tile_mock.monster = mock_monster
        tile_mock.is_portal = False  # Added for MoveCommand check
        tile_mock.portal_to_floor_id = None  # Added for MoveCommand check
        self.mock_world_map.get_tile.return_value = tile_mock
        self.mock_world_map.is_valid_move.return_value = True
        result = self.common_process_command(("move", "north"))
        self.mock_player.move.assert_not_called()
        self.message_log.add_message.assert_any_call(
            f"You bump into a {mock_monster.name}!"
        )
        self.assertFalse(result["game_over"])

    def test_process_command_take_item_exists(self):
        mock_item = MagicMock(spec=Item)
        mock_item.name = "Potion"
        mock_item.properties = {"type": "heal"}
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = mock_item
        self.mock_world_map.get_tile.return_value = tile_mock
        self.mock_world_map.remove_item.return_value = mock_item
        result = self.common_process_command(("take", "Potion"))
        self.mock_world_map.remove_item.assert_called_once_with(
            self.mock_player.x, self.mock_player.y
        )
        self.mock_player.take_item.assert_called_once_with(mock_item)
        self.message_log.add_message.assert_any_call(f"You take the {mock_item.name}.")
        self.assertFalse(result["game_over"])

    def test_process_command_take_quest_item_win(self):
        self.mock_player.x = self.win_pos[0]
        self.mock_player.y = self.win_pos[1]
        self.mock_player.current_floor_id = self.win_pos[2]
        quest_item = MagicMock(spec=Item)
        quest_item.name = "Amulet of Yendor"
        quest_item.properties = {"type": "quest"}
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = quest_item
        self.mock_world_map.get_tile.return_value = tile_mock
        self.mock_world_map.remove_item.return_value = quest_item
        result = self.common_process_command(("take", "Amulet of Yendor"))
        self.message_log.add_message.assert_any_call(
            "You picked up the Amulet of Yendor! You win!"
        )
        self.assertTrue(result["game_over"])

    def test_process_command_take_no_item(self):
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = None
        self.mock_world_map.get_tile.return_value = tile_mock
        result = self.common_process_command(("take", "NonExistent"))
        self.mock_world_map.remove_item.assert_not_called()
        self.mock_player.take_item.assert_not_called()
        self.message_log.add_message.assert_any_call(
            "There is no NonExistent here to take."
        )
        self.assertFalse(result["game_over"])

    def test_process_command_drop_item_space_available(self):
        mock_item_to_drop = MagicMock(spec=Item)
        mock_item_to_drop.name = "Sword"
        self.mock_player.drop_item.return_value = mock_item_to_drop
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = None
        self.mock_world_map.get_tile.return_value = tile_mock
        result = self.common_process_command(("drop", "Sword"))
        self.mock_player.drop_item.assert_called_once_with("Sword")
        self.mock_world_map.place_item.assert_called_once_with(
            mock_item_to_drop, self.mock_player.x, self.mock_player.y
        )
        self.message_log.add_message.assert_any_call(
            f"You drop the {mock_item_to_drop.name}."
        )
        self.assertFalse(result["game_over"])

    def test_process_command_drop_item_no_space(self):
        mock_item_to_drop = MagicMock(spec=Item)
        mock_item_to_drop.name = "Shield"
        self.mock_player.drop_item.return_value = mock_item_to_drop
        item_on_tile = MagicMock(spec=Item)
        item_on_tile.name = "Rock"
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = item_on_tile
        self.mock_world_map.get_tile.return_value = tile_mock
        result = self.common_process_command(("drop", "Shield"))
        self.mock_player.drop_item.assert_called_once_with("Shield")
        self.mock_world_map.place_item.assert_not_called()
        self.mock_player.take_item.assert_called_once_with(mock_item_to_drop)
        self.message_log.add_message.assert_any_call(
            f"You can't drop {mock_item_to_drop.name} here, space occupied."
        )
        self.assertFalse(result["game_over"])

    def test_process_command_drop_item_player_has_no_such_item(self):
        self.mock_player.drop_item.return_value = None
        result = self.common_process_command(("drop", "Helmet"))
        self.message_log.add_message.assert_any_call("You don't have a Helmet to drop.")
        self.assertFalse(result["game_over"])

    def test_process_command_use_item(self):
        item_name = "Health Potion"
        use_message = "You feel healthier."
        self.mock_player.use_item.return_value = use_message
        self.mock_player.health = 50
        result = self.common_process_command(("use", item_name))
        self.mock_player.use_item.assert_called_once_with(item_name)
        self.message_log.add_message.assert_any_call(use_message)
        self.assertFalse(result["game_over"])

    def test_process_command_attack_monster_defeated(self):
        self.mock_player.x, self.mock_player.y = 1, 1  # Player at (1,1)
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Rat"

        # Setup get_tile to place monster at (2,1) - adjacent to player
        def get_tile_side_effect(x, y):
            tile = MagicMock(spec=Tile)
            tile.item = None
            if x == 2 and y == 1:  # East of player
                tile.monster = mock_monster
            else:
                tile.monster = None
            return tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect
        # self.command_processor._get_adjacent_monsters = MagicMock(...) # Removed

        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 10,
            "monster_defeated": True,
            "monster_name": "Rat",
        }
        result = self.common_process_command(("attack", "Rat"))
        self.mock_player.attack_monster.assert_called_once_with(mock_monster)
        self.message_log.add_message.assert_any_call(
            "You attack the Rat for 10 damage."
        )
        self.message_log.add_message.assert_any_call("You defeated the Rat!")
        self.mock_world_map.remove_monster.assert_called_once_with(2, 1)
        self.assertFalse(result["game_over"])

    def test_process_command_attack_monster_survives_player_survives(self):
        self.mock_player.x, self.mock_player.y = 1, 1
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Orc"

        def get_tile_side_effect(x, y):
            tile = MagicMock(spec=Tile)
            tile.item = None
            if x == 2 and y == 1:
                tile.monster = mock_monster
            else:
                tile.monster = None
            return tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect

        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 5,
            "monster_defeated": False,
            "monster_name": "Orc",
        }
        mock_monster.attack.return_value = {
            "damage_dealt_to_player": 3,
            "player_is_defeated": False,
        }
        result = self.common_process_command(("attack", "Orc"))
        self.mock_player.attack_monster.assert_called_once_with(mock_monster)
        self.message_log.add_message.assert_any_call("You attack the Orc for 5 damage.")
        mock_monster.attack.assert_called_once_with(self.mock_player)
        self.message_log.add_message.assert_any_call(
            "The Orc attacks you for 3 damage."
        )
        self.assertFalse(result["game_over"])

    def test_process_command_attack_monster_survives_player_defeated(self):
        self.mock_player.x, self.mock_player.y = 1, 1
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Dragon"

        def get_tile_side_effect(x, y):
            tile = MagicMock(spec=Tile)
            tile.item = None
            if x == 2 and y == 1:
                tile.monster = mock_monster
            else:
                tile.monster = None
            return tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect

        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 10,
            "monster_defeated": False,
            "monster_name": "Dragon",
        }
        mock_monster.attack.return_value = {
            "damage_dealt_to_player": 50,
            "player_is_defeated": True,
        }
        result = self.common_process_command(("attack", "Dragon"))
        self.message_log.add_message.assert_any_call(
            "You attack the Dragon for 10 damage."
        )
        self.message_log.add_message.assert_any_call(
            "The Dragon attacks you for 50 damage."
        )
        self.message_log.add_message.assert_any_call(
            "You have been defeated. Game Over."
        )
        self.assertTrue(result["game_over"])

    def test_process_command_attack_no_monster_specified_one_nearby(self):
        self.mock_player.x, self.mock_player.y = 1, 1
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Slime"

        def get_tile_side_effect(x, y):  # Monster at (1,2) - South of player
            tile = MagicMock(spec=Tile)
            tile.item = None
            if x == 1 and y == 2:
                tile.monster = mock_monster
            else:
                tile.monster = None
            return tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect

        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 1,
            "monster_defeated": True,
            "monster_name": "Slime",
        }
        result = self.common_process_command(("attack", None))
        self.mock_player.attack_monster.assert_called_once_with(mock_monster)
        self.message_log.add_message.assert_any_call(
            "You attack the Slime for 1 damage."
        )
        self.assertFalse(result["game_over"])

    def test_process_command_attack_no_monster_specified_multiple_nearby(self):
        self.mock_player.x, self.mock_player.y = 1, 1
        mock_monster1 = MagicMock(spec=Monster)
        mock_monster1.name = "Imp"  # West
        mock_monster2 = MagicMock(spec=Monster)
        mock_monster2.name = "Bat"  # East

        def get_tile_side_effect(x, y):
            tile = MagicMock(spec=Tile)
            tile.item = None
            if x == 0 and y == 1:
                tile.monster = mock_monster1
            elif x == 2 and y == 1:
                tile.monster = mock_monster2
            else:
                tile.monster = None
            return tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect

        result = self.common_process_command(("attack", None))
        self.mock_player.attack_monster.assert_not_called()
        self.message_log.add_message.assert_any_call(
            "Multiple monsters nearby: Bat, Imp. Which one?"
        )
        self.assertFalse(result["game_over"])

    def test_process_command_attack_no_monster_nearby(self):
        self.mock_player.x, self.mock_player.y = 1, 1

        def get_tile_side_effect(x, y):  # No monsters adjacent
            tile = MagicMock(spec=Tile)
            tile.item = None
            tile.monster = None
            return tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect
        # self.command_processor._get_adjacent_monsters = MagicMock(return_value=[])
        # # Removed

        result = self.common_process_command(("attack", None))
        self.message_log.add_message.assert_any_call(
            "There is no monster nearby to attack."
        )
        self.assertFalse(result["game_over"])

    def test_process_command_attack_specified_monster_not_found(self):
        self.mock_player.x, self.mock_player.y = 1, 1
        mock_monster_present = MagicMock(spec=Monster)
        mock_monster_present.name = "Wolf"  # Present at (0,1)

        def get_tile_side_effect(x, y):
            tile = MagicMock(spec=Tile)
            tile.item = None
            if x == 0 and y == 1:
                tile.monster = mock_monster_present
            else:
                tile.monster = None
            return tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect
        # self.command_processor._get_adjacent_monsters = MagicMock(...) # Removed

        result = self.common_process_command(("attack", "Ghost"))
        self.message_log.add_message.assert_any_call("No monster named 'Ghost' nearby.")
        self.assertFalse(result["game_over"])

    def test_process_command_inventory_has_items(self):
        item1 = MagicMock(spec=Item)
        item1.name = "Dagger"
        item2 = MagicMock(spec=Item)
        item2.name = "Rope"
        self.mock_player.inventory = [item1, item2]
        result = self.common_process_command(("inventory", None))
        self.message_log.add_message.assert_any_call("Inventory: Dagger, Rope")
        self.assertFalse(result["game_over"])

    def test_process_command_inventory_empty(self):
        self.mock_player.inventory = []
        result = self.common_process_command(("inventory", None))
        self.message_log.add_message.assert_any_call("Your inventory is empty.")
        self.assertFalse(result["game_over"])

    def test_process_command_look_clear_area(self):
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = None
        tile_mock.monster = None  # Monster on current tile

        # For _get_adjacent_monsters, need side_effect if checking other tiles
        def get_tile_side_effect(x, y):
            # If it's player's current tile
            if x == self.mock_player.x and y == self.mock_player.y:
                return tile_mock
            # For adjacent tiles, assume they are empty of monsters
            # for this specific test
            adj_tile = MagicMock(spec=Tile)
            adj_tile.item = None
            adj_tile.monster = None
            return adj_tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect
        # self.command_processor._get_adjacent_monsters = MagicMock(return_value=[])
        # # Removed
        result = self.common_process_command(("look", None))
        self.message_log.add_message.assert_any_call(
            f"You are at ({self.mock_player.x}, {self.mock_player.y}) on floor {self.mock_player.current_floor_id}."
        )
        self.message_log.add_message.assert_any_call("The area is clear.")
        self.assertFalse(result["game_over"])

    def test_process_command_look_item_present(self):
        mock_item = MagicMock(spec=Item)
        mock_item.name = "Key"
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = mock_item
        tile_mock.monster = None
        self.mock_world_map.get_tile.return_value = tile_mock
        self.command_processor._get_adjacent_monsters = MagicMock(return_value=[])
        self.common_process_command(("look", None))
        self.message_log.add_message.assert_any_call(
            f"You see a {mock_item.name} here."
        )

    def test_process_command_look_monster_present_on_tile(self):
        mock_monster_on_tile = MagicMock(spec=Monster)
        mock_monster_on_tile.name = "Spider"
        tile_mock = MagicMock(spec=Tile)
        tile_mock.item = None
        tile_mock.monster = mock_monster_on_tile
        self.mock_world_map.get_tile.return_value = tile_mock
        self.command_processor._get_adjacent_monsters = MagicMock(return_value=[])
        self.common_process_command(("look", None))
        self.message_log.add_message.assert_any_call(
            f"There is a {mock_monster_on_tile.name} here!"
        )

    def test_process_command_look_adjacent_monster(self):
        self.mock_player.x, self.mock_player.y = 1, 1
        current_tile_mock = MagicMock(spec=Tile)  # Player's current tile
        current_tile_mock.item = None
        current_tile_mock.monster = None

        mock_adj_monster = MagicMock(spec=Monster)
        mock_adj_monster.name = "Zombie"

        adj_monster_x, adj_monster_y = 1, 2  # South of player at (1,1)

        def get_tile_side_effect(x, y):
            if x == self.mock_player.x and y == self.mock_player.y:
                return current_tile_mock
            elif x == adj_monster_x and y == adj_monster_y:
                adj_tile = MagicMock(spec=Tile)
                adj_tile.item = None
                adj_tile.monster = mock_adj_monster
                return adj_tile
            else:  # Other adjacent tiles are empty
                empty_tile = MagicMock(spec=Tile)
                empty_tile.item = None
                empty_tile.monster = None
                return empty_tile

        self.mock_world_map.get_tile.side_effect = get_tile_side_effect
        # self.command_processor._get_adjacent_monsters = MagicMock(...) # Removed

        self.common_process_command(("look", None))
        self.message_log.add_message.assert_any_call(
            f"You see a {mock_adj_monster.name} at ({adj_monster_x}, {adj_monster_y})."
        )

    def test_process_command_quit(self):
        result = self.common_process_command(("quit", None))
        self.message_log.add_message.assert_any_call("Quitting game.")
        self.assertTrue(result["game_over"])

    def test_process_command_none_tuple(self):
        result = self.common_process_command(None)
        self.message_log.add_message.assert_any_call("Unknown command.")
        self.assertFalse(result["game_over"])


if __name__ == "__main__":
    unittest.main()

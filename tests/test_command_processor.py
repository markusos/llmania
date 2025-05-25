import unittest
from unittest.mock import MagicMock

# Assuming src is in PYTHONPATH or tests are run in a way that src can be imported
from src.command_processor import CommandProcessor
from src.item import Item  # For creating dummy items
from src.monster import Monster  # For type hinting and mocking spec
from src.player import Player  # For type hinting and mocking spec
from src.world_map import WorldMap  # For type hinting and mocking spec


class TestCommandProcessor(unittest.TestCase):
    def setUp(self):
        self.command_processor = CommandProcessor()

        # Mock dependencies
        self.mock_player = MagicMock(spec=Player)
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.health = 100
        self.mock_player.inventory = []

        self.mock_world_map = MagicMock(spec=WorldMap)
        self.mock_world_map.get_tile = MagicMock()
        self.mock_world_map.is_valid_move = MagicMock(return_value=True)
        self.mock_world_map.remove_item = MagicMock()
        self.mock_world_map.place_item = MagicMock()
        self.mock_world_map.remove_monster = MagicMock()

        self.message_log = []
        self.win_pos = (10, 10)  # Example win position

    def common_process_command(self, command_tuple):
        return self.command_processor.process_command(
            command_tuple,
            self.mock_player,
            self.mock_world_map,
            self.message_log,
            self.win_pos,
        )

    # --- Tests for _get_adjacent_monsters ---
    def test_get_adjacent_monsters(self):
        # Setup map with monsters
        mock_monster1 = MagicMock(spec=Monster, name="Goblin1")
        # mock_monster2 = MagicMock(spec=Monster, name="Goblin2") # Unused variable

        # Tile returns
        # (0,1) North, (2,1) South, (1,0) West, (1,2) East
        # Player at (1,1)
        # Monster at (1,0) (West of player) and (2,1) (South of player)

        def get_tile_side_effect(x, y):
            tile_mock = MagicMock()
            if (x, y) == (1, 0):  # West
                tile_mock.monster = mock_monster1
            elif (x, y) == (
                2,
                1,
            ):  # South. ERROR in logic: this should be (1,2) for south of (1,1)
                # Correcting: player is at (1,1)
                # N:(1,0), S:(1,2), W:(0,1), E:(2,1)
                # Let's say monster is at (1,2) (South) and (0,1) (West)
                # This was the old logic for _get_adj_monsters for game_engine.
                # New logic for command_processor is:
                # (0,-1)N, (0,1)S, (-1,0)W, (1,0)E relative to player
                # Player at (1,1) => N(1,0), S(1,2), W(0,1), E(2,1)
                # Monster at (1,0) (North) and (2,1) (East)
                tile_mock.monster = None  # Default
            else:
                tile_mock.monster = None
            return tile_mock

        # Re-setup for clarity for _get_adjacent_monsters test
        player_x, player_y = 5, 5
        # Monsters at (5,4) (North) and (6,5) (East)
        monster_north = MagicMock(spec=Monster)
        monster_east = MagicMock(spec=Monster)

        def get_tile_for_adj_test(x, y):
            m_tile = MagicMock()
            if x == 5 and y == 4:  # North
                m_tile.monster = monster_north
            elif x == 6 and y == 5:  # East
                m_tile.monster = monster_east
            else:
                m_tile.monster = None
            return m_tile

        self.mock_world_map.get_tile.side_effect = get_tile_for_adj_test

        adj_monsters = self.command_processor._get_adjacent_monsters(
            player_x, player_y, self.mock_world_map
        )

        self.assertEqual(len(adj_monsters), 2)
        self.assertIn((monster_north, 5, 4), adj_monsters)
        self.assertIn((monster_east, 6, 5), adj_monsters)

    # --- Tests for process_command ---
    def test_process_command_move_valid(self):
        self.mock_world_map.get_tile.return_value = MagicMock(
            monster=None
        )  # No monster at destination
        result = self.common_process_command(("move", "north"))

        self.mock_player.move.assert_called_once_with(0, -1)
        self.assertIn("You move north.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_move_invalid_wall(self):
        self.mock_world_map.is_valid_move.return_value = False
        result = self.common_process_command(("move", "east"))

        self.mock_player.move.assert_not_called()
        self.assertIn("You can't move there.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_move_into_monster(self):
        # Player at (1,1), attempts to move to (1,0) (north)
        # Monster is at (1,0)
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Goblin"  # Ensure .name attribute is set
        self.mock_world_map.get_tile.return_value = MagicMock(monster=mock_monster)
        self.mock_world_map.is_valid_move.return_value = (
            True  # Path is "valid" but occupied by monster
        )

        result = self.common_process_command(("move", "north"))

        self.mock_player.move.assert_not_called()  # Should not move into monster
        self.assertIn(f"You bump into a {mock_monster.name}!", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_take_item_exists(self):
        mock_item = MagicMock(spec=Item, properties={"type": "heal"})
        mock_item.name = "Potion"  # Ensure .name attribute is set
        self.mock_world_map.get_tile.return_value = MagicMock(item=mock_item)
        self.mock_world_map.remove_item.return_value = mock_item  # Successfully removed

        result = self.common_process_command(("take", "Potion"))

        self.mock_world_map.remove_item.assert_called_once_with(
            self.mock_player.x, self.mock_player.y
        )
        self.mock_player.take_item.assert_called_once_with(mock_item)
        self.assertIn(f"You take the {mock_item.name}.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_take_quest_item_win(self):
        # Player at win_pos
        self.mock_player.x, self.mock_player.y = self.win_pos
        quest_item = MagicMock(spec=Item, properties={"type": "quest"})
        quest_item.name = "Amulet"  # Ensure .name attribute is set
        self.mock_world_map.get_tile.return_value = MagicMock(item=quest_item)
        self.mock_world_map.remove_item.return_value = quest_item

        result = self.common_process_command(("take", "Amulet"))

        self.assertIn("You picked up the Amulet of Yendor! You win!", self.message_log)
        self.assertTrue(result["game_over"])

    def test_process_command_take_no_item(self):
        self.mock_world_map.get_tile.return_value = MagicMock(
            item=None
        )  # No item on tile
        result = self.common_process_command(("take", "NonExistent"))

        self.mock_world_map.remove_item.assert_not_called()
        self.mock_player.take_item.assert_not_called()
        self.assertIn("There is no NonExistent here to take.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_drop_item_space_available(self):
        mock_item_to_drop = MagicMock(spec=Item)
        mock_item_to_drop.name = "Sword"  # Ensure .name attribute is set
        self.mock_player.drop_item.return_value = mock_item_to_drop  # Player drops it
        self.mock_world_map.get_tile.return_value = MagicMock(
            item=None
        )  # Space available

        result = self.common_process_command(("drop", "Sword"))

        self.mock_player.drop_item.assert_called_once_with("Sword")
        self.mock_world_map.place_item.assert_called_once_with(
            mock_item_to_drop, self.mock_player.x, self.mock_player.y
        )
        self.assertIn(f"You drop the {mock_item_to_drop.name}.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_drop_item_no_space(self):
        mock_item_to_drop = MagicMock(spec=Item)
        mock_item_to_drop.name = "Shield"  # Ensure .name attribute is set
        self.mock_player.drop_item.return_value = mock_item_to_drop
        self.mock_world_map.get_tile.return_value = MagicMock(
            item=MagicMock(spec=Item)
        )  # Space occupied

        result = self.common_process_command(("drop", "Shield"))

        self.mock_player.drop_item.assert_called_once_with("Shield")
        self.mock_world_map.place_item.assert_not_called()
        self.mock_player.take_item.assert_called_once_with(
            mock_item_to_drop
        )  # Player takes it back
        self.assertIn(
            f"You can't drop {mock_item_to_drop.name} here, space occupied.",
            self.message_log,
        )
        self.assertFalse(result["game_over"])

    def test_process_command_drop_item_player_has_no_such_item(self):
        self.mock_player.drop_item.return_value = None  # Player doesn't have it
        result = self.common_process_command(("drop", "Helmet"))
        self.assertIn("You don't have a Helmet to drop.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_use_item(self):
        item_name = "Health Potion"
        use_message = "You feel healthier."
        self.mock_player.use_item.return_value = use_message
        self.mock_player.health = 50  # Ensure player is alive before use

        result = self.common_process_command(("use", item_name))

        self.mock_player.use_item.assert_called_once_with(item_name)
        self.assertIn(use_message, self.message_log)
        self.assertFalse(
            result["game_over"]
        )  # Assuming normal item use doesn't end game

    def test_process_command_use_item_cursed_kills_player(self):
        item_name = "Cursed Ring"
        use_message = "The Cursed Ring drains your life!"
        self.mock_player.use_item.return_value = use_message

        # Simulate player health dropping to 0 after use_item
        def side_effect_use_item(item_name_arg):
            if item_name_arg == item_name:
                self.mock_player.health = 0
            return use_message

        self.mock_player.use_item.side_effect = side_effect_use_item

        result = self.common_process_command(("use", item_name))

        self.assertIn(use_message, self.message_log)
        self.assertIn(
            "You have succumbed to a cursed item! Game Over.", self.message_log
        )
        self.assertTrue(result["game_over"])

    def test_process_command_attack_monster_defeated(self):
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Rat"  # Set the attribute
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[(mock_monster, 2, 1)]
        )

        # Player attacks, monster is defeated
        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 10,
            "monster_defeated": True,
            "monster_name": "Rat",
        }

        result = self.common_process_command(("attack", "Rat"))

        self.mock_player.attack_monster.assert_called_once_with(mock_monster)
        self.assertIn("You attack the Rat for 10 damage.", self.message_log)
        self.assertIn("You defeated the Rat!", self.message_log)
        self.mock_world_map.remove_monster.assert_called_once_with(2, 1)
        self.assertFalse(result["game_over"])

    def test_process_command_attack_monster_survives_player_survives(self):
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Orc"  # Ensure .name attribute is set
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[(mock_monster, 2, 1)]
        )

        # Player attacks, monster survives
        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 5,
            "monster_defeated": False,
            "monster_name": "Orc",
        }
        # Monster attacks back, player survives
        mock_monster.attack.return_value = {
            "damage_dealt_to_player": 3,
            "player_is_defeated": False,
        }

        result = self.common_process_command(("attack", "Orc"))

        self.mock_player.attack_monster.assert_called_once_with(mock_monster)
        self.assertIn("You attack the Orc for 5 damage.", self.message_log)
        mock_monster.attack.assert_called_once_with(self.mock_player)
        self.assertIn("The Orc attacks you for 3 damage.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_attack_monster_survives_player_defeated(self):
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Dragon"  # Ensure .name attribute is set
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[(mock_monster, 2, 1)]
        )

        # Player attacks, monster survives
        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 10,
            "monster_defeated": False,
            "monster_name": "Dragon",
        }
        # Monster attacks back, player is defeated
        mock_monster.attack.return_value = {
            "damage_dealt_to_player": 50,
            "player_is_defeated": True,
        }

        result = self.common_process_command(("attack", "Dragon"))

        self.assertIn("You attack the Dragon for 10 damage.", self.message_log)
        self.assertIn("The Dragon attacks you for 50 damage.", self.message_log)
        self.assertIn("You have been defeated. Game Over.", self.message_log)
        self.assertTrue(result["game_over"])

    def test_process_command_attack_no_monster_specified_one_nearby(self):
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Slime"  # Ensure .name attribute is set
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[(mock_monster, 1, 2)]
        )
        self.mock_player.attack_monster.return_value = {
            "damage_dealt": 1,
            "monster_defeated": True,
            "monster_name": "Slime",
        }

        result = self.common_process_command(
            ("attack", None)
        )  # No argument for monster name
        self.mock_player.attack_monster.assert_called_once_with(mock_monster)
        self.assertIn("You attack the Slime for 1 damage.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_attack_no_monster_specified_multiple_nearby(self):
        mock_monster1 = MagicMock(spec=Monster)
        mock_monster1.name = "Imp"  # Ensure .name attribute is set
        mock_monster2 = MagicMock(spec=Monster)
        mock_monster2.name = "Bat"  # Ensure .name attribute is set
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[(mock_monster1, 0, 1), (mock_monster2, 2, 1)]
        )

        result = self.common_process_command(("attack", None))
        self.mock_player.attack_monster.assert_not_called()
        self.assertIn(
            "Multiple monsters nearby: Bat, Imp. Which one?", self.message_log
        )  # Sorted list
        self.assertFalse(result["game_over"])

    def test_process_command_attack_no_monster_nearby(self):
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[]
        )  # No monsters
        result = self.common_process_command(("attack", None))
        self.assertIn("There is no monster nearby to attack.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_attack_specified_monster_not_found(self):
        mock_monster_present = MagicMock(spec=Monster)
        mock_monster_present.name = "Wolf"  # Ensure .name attribute is set
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[(mock_monster_present, 0, 1)]
        )
        result = self.common_process_command(
            ("attack", "Ghost")
        )  # Attack 'Ghost', but only 'Wolf' is present
        self.assertIn("There is no monster named Ghost nearby.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_inventory_has_items(self):
        item1 = MagicMock(spec=Item)
        item1.name = "Dagger"  # Ensure .name attribute is set
        item2 = MagicMock(spec=Item)
        item2.name = "Rope"  # Ensure .name attribute is set
        self.mock_player.inventory = [item1, item2]

        result = self.common_process_command(("inventory", None))
        self.assertIn("Inventory: Dagger, Rope", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_inventory_empty(self):
        self.mock_player.inventory = []
        result = self.common_process_command(("inventory", None))
        self.assertIn("Your inventory is empty.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_look_clear_area(self):
        # Player at (1,1). Tile has no item, no monster. No adjacent monsters.
        self.mock_world_map.get_tile.return_value = MagicMock(item=None, monster=None)
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[]
        )  # No adjacent monsters

        result = self.common_process_command(
            ("look", None)
        )  # Restore result assignment

        self.assertIn("You are at (1, 1).", self.message_log)
        self.assertIn("The area is clear.", self.message_log)
        self.assertFalse(result["game_over"])

    def test_process_command_look_item_present(self):
        mock_item = MagicMock(spec=Item)
        mock_item.name = "Key"  # Ensure .name attribute is set
        self.mock_world_map.get_tile.return_value = MagicMock(
            item=mock_item, monster=None
        )
        self.command_processor._get_adjacent_monsters = MagicMock(return_value=[])

        self.common_process_command(("look", None))
        self.assertIn(f"You see a {mock_item.name} here.", self.message_log)

    def test_process_command_look_monster_present_on_tile(self):
        mock_monster_on_tile = MagicMock(spec=Monster)
        mock_monster_on_tile.name = "Spider"  # Ensure .name attribute is set
        self.mock_world_map.get_tile.return_value = MagicMock(
            item=None, monster=mock_monster_on_tile
        )
        self.command_processor._get_adjacent_monsters = MagicMock(return_value=[])

        self.common_process_command(("look", None))
        self.assertIn(f"There is a {mock_monster_on_tile.name} here!", self.message_log)

    def test_process_command_look_adjacent_monster(self):
        self.mock_world_map.get_tile.return_value = MagicMock(
            item=None, monster=None
        )  # Current tile clear
        mock_adj_monster = MagicMock(spec=Monster)
        mock_adj_monster.name = "Zombie"  # Ensure .name attribute is set
        # _get_adjacent_monsters will be called by the 'look' logic itself.
        # So, we mock its return value directly for the CommandProcessor instance.
        self.command_processor._get_adjacent_monsters = MagicMock(
            return_value=[(mock_adj_monster, 1, 2)]
        )

        self.common_process_command(("look", None))
        self.assertIn(f"You see a {mock_adj_monster.name} at (1, 2).", self.message_log)

    def test_process_command_quit(self):
        result = self.common_process_command(("quit", None))
        self.assertIn("Quitting game.", self.message_log)
        self.assertTrue(result["game_over"])

    def test_process_command_none_tuple(self):
        result = self.common_process_command(None)
        self.assertIn("Unknown command.", self.message_log)
        self.assertFalse(result["game_over"])


if __name__ == "__main__":
    unittest.main()

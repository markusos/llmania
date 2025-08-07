import json
import random
import unittest
from unittest.mock import MagicMock

from src.commands.use_command import UseCommand
from src.item_factory import ItemFactory
from src.message_log import MessageLog
from src.player import Player
from src.tile import Tile
from src.world_map import WorldMap


class TestUseCommand(unittest.TestCase):
    def setUp(self):
        self.item_factory = ItemFactory("src/data/items.json")
        self.player = Player(x=5, y=5, current_floor_id=0, health=100)
        self.world_map = WorldMap(width=20, height=20)
        self.message_log = MessageLog()
        self.game_engine = MagicMock()
        self.game_engine.world_map = self.world_map
        self.game_engine.player = self.player
        self.game_engine.message_log = self.message_log
        self.game_engine.item_factory = self.item_factory
        self.game_engine.world_maps = {0: self.world_map}
        self.game_engine.random = random.Random(12345)
        self.winning_position = (10, 10, 0)
        for y in range(20):
            for x in range(20):
                self.world_map.grid[y][x] = Tile(tile_type="floor")

    def test_all_items_can_be_created(self):
        item_factory = ItemFactory("src/data/items.json")
        with open("src/data/items.json", encoding="utf-8") as f:
            item_data = json.load(f)
        for item_key in item_data:
            with self.subTest(item_key=item_key):
                item = item_factory.create_item(item_key)
                self.assertIsNotNone(item)

    def test_use_health_potion(self):
        # Arrange
        self.player.health = 50
        health_potion = self.item_factory.create_item("health_potion")
        self.player.inventory.append(health_potion)
        command = UseCommand(
            self.player,
            self.world_map,
            self.message_log,
            self.winning_position,
            argument="Health Potion",
            game_engine=self.game_engine,
        )

        # Act
        command.execute()

        # Assert
        self.assertEqual(self.player.health, 60)
        self.assertIn(
            "You feel a warm glow and recover 10 HP.", self.message_log.messages[-1]
        )

    def test_use_scroll_of_teleportation(self):
        # Arrange
        scroll = self.item_factory.create_item("scroll_of_teleportation")
        self.player.inventory.append(scroll)
        initial_pos = (self.player.x, self.player.y)
        command = UseCommand(
            self.player,
            self.world_map,
            self.message_log,
            self.winning_position,
            argument="Scroll of Teleportation",
            game_engine=self.game_engine,
        )

        # Act
        command.execute()

        # Assert
        self.assertNotEqual((self.player.x, self.player.y), initial_pos)
        self.assertIn(
            "You were teleported to a new location.", self.message_log.messages[-1]
        )

    def test_toggle_equip_item(self):
        # Arrange
        sword = self.item_factory.create_item("sword")
        self.player.inventory.append(sword)
        command = UseCommand(
            self.player,
            self.world_map,
            self.message_log,
            self.winning_position,
            argument="Sword",
            game_engine=self.game_engine,
        )

        # Act: Equip
        command.execute()

        # Assert: Equip
        self.assertEqual(self.player.equipment["main_hand"], sword)
        self.assertIn("Equipped Sword.", self.message_log.messages[-1])

        # Act: Unequip
        command.execute()

        # Assert: Unequip
        self.assertIsNone(self.player.equipment["main_hand"])
        self.assertIn("You unequip Sword.", self.message_log.messages[-1])

    def test_use_fire_potion(self):
        # Arrange
        fire_potion = self.item_factory.create_item("fire_potion")
        self.player.inventory.append(fire_potion)
        command = UseCommand(
            self.player,
            self.world_map,
            self.message_log,
            self.winning_position,
            argument="Fire Potion",
            game_engine=self.game_engine,
        )

        # Act
        command.execute()

        # Assert
        # The damage effect is not implemented, so health should not change
        self.assertEqual(self.player.health, 100)
        self.assertIn(
            "The item crackles with power, ready to be thrown.",
            self.message_log.messages[-1],
        )

    def test_use_invisibility_potion(self):
        # Arrange
        invisibility_potion = self.item_factory.create_item("invisibility_potion")
        self.player.inventory.append(invisibility_potion)
        command = UseCommand(
            self.player,
            self.world_map,
            self.message_log,
            self.winning_position,
            argument="Invisibility Potion",
            game_engine=self.game_engine,
        )

        # Act
        command.execute()

        # Assert
        self.assertGreater(self.player.invisibility_turns, 0)
        self.assertIn(
            "You drink the potion and become invisible for 10 turns.",
            self.message_log.messages[-1],
        )

    def test_equip_amulet_of_health(self):
        # Arrange
        amulet = self.item_factory.create_item("amulet_of_health")
        self.player.inventory.append(amulet)
        initial_max_health = self.player.get_max_health()
        command = UseCommand(
            self.player,
            self.world_map,
            self.message_log,
            self.winning_position,
            argument="Amulet of Health",
            game_engine=self.game_engine,
        )

        # Act
        command.execute()

        # Assert
        self.assertEqual(self.player.equipment["amulet"], amulet)
        self.assertGreater(self.player.get_max_health(), initial_max_health)
        self.assertIn("Equipped Amulet of Health.", self.message_log.messages[-1])


if __name__ == "__main__":
    unittest.main()

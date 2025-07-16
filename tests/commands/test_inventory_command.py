import unittest
from unittest.mock import MagicMock

from src.commands.inventory_command import InventoryCommand
from src.equippable import Equippable
from src.item import Item
from src.message_log import MessageLog
from src.player import Player
from src.world_map import WorldMap


class TestInventoryCommand(unittest.TestCase):
    def setUp(self):
        self.player = Player(x=1, y=1, current_floor_id=0, health=10)
        self.world_map = WorldMap(width=10, height=10)
        self.message_log = MagicMock(spec=MessageLog)
        self.winning_position = (9, 9, 0)

    def test_inventory_empty(self):
        cmd = InventoryCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=self.winning_position,
        )
        result = cmd.execute()
        self.message_log.add_message.assert_called_with("Your inventory is empty.")
        self.assertFalse(result.get("game_over", False))

    def test_inventory_with_items_not_equipped(self):
        self.player.inventory.append(Item("Potion", "A healing potion", {}))
        self.player.inventory.append(Item("Scroll", "A magic scroll", {}))
        cmd = InventoryCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=self.winning_position,
        )
        result = cmd.execute()
        self.message_log.add_message.assert_called_with("Inventory: Potion, Scroll")
        self.assertFalse(result.get("game_over", False))

    def test_inventory_with_equipped_weapon(self):
        weapon = Equippable(
            "Sword",
            "A sharp sword",
            {"slot": "main_hand", "attack_bonus": 5},
        )
        self.player.inventory.append(weapon)
        self.player.equipment["main_hand"] = weapon
        cmd = InventoryCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=self.winning_position,
        )
        result = cmd.execute()
        self.message_log.add_message.assert_called_with("Inventory: Sword (equipped)")
        self.assertFalse(result.get("game_over", False))

    def test_inventory_with_equipped_shield(self):
        shield = Equippable(
            "Shield",
            "A sturdy shield",
            {"slot": "off_hand", "defense_bonus": 5},
        )
        self.player.inventory.append(shield)
        self.player.equipment["off_hand"] = shield
        cmd = InventoryCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=self.winning_position,
        )
        result = cmd.execute()
        self.message_log.add_message.assert_called_with("Inventory: Shield (equipped)")
        self.assertFalse(result.get("game_over", False))

    def test_inventory_with_equipped_helmet(self):
        helmet = Equippable(
            "Helmet",
            "A sturdy helmet",
            {"slot": "head", "defense_bonus": 3},
        )
        self.player.inventory.append(helmet)
        self.player.equipment["head"] = helmet
        cmd = InventoryCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=self.winning_position,
        )
        result = cmd.execute()
        self.message_log.add_message.assert_called_with("Inventory: Helmet (equipped)")
        self.assertFalse(result.get("game_over", False))


if __name__ == "__main__":
    unittest.main()

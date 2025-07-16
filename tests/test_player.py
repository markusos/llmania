import unittest
from unittest.mock import MagicMock

from src.equippable import Equippable
from src.item import Item
from src.monster import Monster
from src.player import Player


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player(x=1, y=2, health=100, current_floor_id=0)

    def test_player_initialization(self):
        self.assertEqual(self.player.x, 1)
        self.assertEqual(self.player.y, 2)
        self.assertEqual(self.player.health, 100)
        self.assertEqual(self.player.inventory, [])
        self.assertEqual(self.player.base_attack_power, 2)
        self.assertIsNone(self.player.equipment["main_hand"])

    def test_player_move(self):
        self.player.move(1, -1)
        self.assertEqual(self.player.x, 2)
        self.assertEqual(self.player.y, 1)

    def test_player_take_item(self):
        potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
        self.player.take_item(potion)
        self.assertIn(potion, self.player.inventory)

    def test_player_drop_item(self):
        potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
        self.player.take_item(potion)
        dropped_item = self.player.drop_item("Potion")
        self.assertEqual(dropped_item, potion)
        self.assertNotIn(potion, self.player.inventory)

    def test_player_use_item_heal(self):
        self.player.health = 50
        potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
        self.player.take_item(potion)
        self.player.use_item("Potion")
        self.assertEqual(self.player.health, 60)
        self.assertNotIn(potion, self.player.inventory)

    def test_equip_and_unequip_item(self):
        sword = Equippable(
            "Sword",
            "A sharp blade",
            {"type": "weapon", "attack_bonus": 5, "slot": "main_hand"},
        )
        self.player.take_item(sword)
        message = self.player.use_item("Sword")
        self.assertEqual(message, "Equipped Sword.")
        self.assertEqual(self.player.equipment["main_hand"], sword)

        message = self.player.use_item("Sword")
        self.assertEqual(message, "You unequip Sword.")
        self.assertIsNone(self.player.equipment["main_hand"])

    def test_get_attack_power(self):
        self.assertEqual(self.player.get_attack_power(), 2)
        sword = Equippable(
            "Sword",
            "A sharp blade",
            {"type": "weapon", "attack_bonus": 5, "slot": "main_hand"},
        )
        self.player.take_item(sword)
        self.player.use_item("Sword")
        self.assertEqual(self.player.get_attack_power(), 7)

    def test_attack_monster(self):
        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Goblin"
        mock_monster.take_damage.return_value = {"defeated": False}
        self.player.attack_monster(mock_monster)
        mock_monster.take_damage.assert_called_once_with(2)

        sword = Equippable(
            "Sword",
            "A sharp blade",
            {"type": "weapon", "attack_bonus": 5, "slot": "main_hand"},
        )
        self.player.take_item(sword)
        self.player.use_item("Sword")
        self.player.attack_monster(mock_monster)
        mock_monster.take_damage.assert_called_with(7)

    def test_player_take_damage(self):
        result = self.player.take_damage(20)
        self.assertEqual(self.player.health, 80)
        self.assertEqual(result, {"damage_taken": 20, "is_defeated": False})

        result = self.player.take_damage(90)
        self.assertEqual(self.player.health, 0)
        self.assertEqual(result, {"damage_taken": 90, "is_defeated": True})

    def test_get_defense(self):
        self.assertEqual(self.player.get_defense(), 0)
        helmet = Equippable(
            "Helmet",
            "A basic helmet.",
            {"type": "armor", "defense_bonus": 1, "slot": "head"},
        )
        self.player.take_item(helmet)
        self.player.use_item("Helmet")
        self.assertEqual(self.player.get_defense(), 1)

    def test_get_speed(self):
        self.assertEqual(self.player.get_speed(), 1)
        boots = Equippable(
            "Boots of Speed",
            "Boots that increase your movement speed.",
            {"type": "boots", "speed_bonus": 1, "slot": "boots"},
        )
        self.player.take_item(boots)
        self.player.use_item("Boots of Speed")
        self.assertEqual(self.player.get_speed(), 2)

    def test_use_invisibility_potion(self):
        potion = Item(
            "Invisibility Potion",
            "Makes you invisible.",
            {"type": "invisibility", "duration": 10},
        )
        self.player.take_item(potion)
        self.player.use_item("Invisibility Potion")
        self.assertEqual(self.player.invisibility_turns, 10)

    def test_equip_amulet_of_health(self):
        amulet = Equippable(
            "Amulet of Health",
            "Increases max health.",
            {"type": "amulet", "max_health_bonus": 10, "slot": "amulet"},
        )
        self.player.take_item(amulet)
        initial_max_health = self.player.max_health
        self.player.use_item("Amulet of Health")
        self.assertEqual(self.player.max_health, initial_max_health + 10)


if __name__ == "__main__":
    unittest.main()

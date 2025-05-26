import unittest
from unittest.mock import MagicMock

from src.item import Item
from src.monster import Monster  # For type hinting and mocking spec
from src.player import Player


class TestPlayer(unittest.TestCase):
    def test_player_initialization(self):
        player = Player(x=1, y=2, health=100)
        self.assertEqual(player.x, 1)
        self.assertEqual(player.y, 2)
        self.assertEqual(player.health, 100)
        self.assertEqual(player.inventory, [])
        self.assertEqual(player.base_attack_power, 2)
        self.assertIsNone(player.equipped_weapon)

    def test_player_move(self):
        player = Player(x=5, y=5, health=100)
        player.move(1, -1)
        self.assertEqual(player.x, 6)
        self.assertEqual(player.y, 4)
        player.move(-2, 3)
        self.assertEqual(player.x, 4)
        self.assertEqual(player.y, 7)

    def test_player_take_item(self):
        player = Player(x=0, y=0, health=50)
        potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
        player.take_item(potion)
        self.assertEqual(len(player.inventory), 1)
        self.assertIn(potion, player.inventory)
        self.assertEqual(player.inventory[0].name, "Potion")

    def test_player_drop_item_found(self):
        player = Player(x=0, y=0, health=50)
        potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
        sword = Item("Sword", "A sharp blade", {"type": "weapon", "attack_bonus": 5})
        player.take_item(potion)
        player.take_item(sword)

        dropped_item = player.drop_item("Potion")
        self.assertIsNotNone(dropped_item)
        self.assertEqual(dropped_item.name, "Potion")
        self.assertEqual(len(player.inventory), 1)
        self.assertEqual(player.inventory[0].name, "Sword")

        dropped_item_2 = player.drop_item("Sword")
        self.assertIsNotNone(dropped_item_2)
        self.assertEqual(dropped_item_2.name, "Sword")
        self.assertEqual(len(player.inventory), 0)

    def test_player_drop_item_not_found(self):
        player = Player(x=0, y=0, health=50)
        potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
        player.take_item(potion)

        dropped_item = player.drop_item("NonExistentItem")
        self.assertIsNone(dropped_item)
        self.assertEqual(len(player.inventory), 1)

    def test_player_use_item_heal(self):
        player = Player(x=0, y=0, health=50)
        player.max_health = 100  # Explicitly set max_health for this test
        potion = Item(
            "Health Potion", "Restores 10 HP.", {"type": "heal", "amount": 10}
        )
        player.take_item(potion)

        result = player.use_item("Health Potion")
        self.assertEqual(player.health, 60)
        self.assertEqual(len(player.inventory), 0)
        self.assertEqual(result, "Used Health Potion, healed by 10 HP.")

    def test_player_use_item_weapon(self):
        player = Player(x=0, y=0, health=100)
        sword = Item(
            "Iron Sword", "A basic sword.", {"type": "weapon", "attack_bonus": 5}
        )
        player.take_item(sword)

        result = player.use_item("Iron Sword")
        self.assertEqual(player.equipped_weapon, sword)
        self.assertEqual(player.equipped_weapon.name, "Iron Sword")
        self.assertEqual(len(player.inventory), 1)  # Weapon stays in inventory
        self.assertEqual(result, "Equipped Iron Sword.")

    def test_player_use_item_unusable_or_not_found(self):
        player = Player(x=0, y=0, health=100)
        rock = Item("Rock", "Just a rock.", {"type": "junk"})
        player.take_item(rock)

        result_unusable = player.use_item("Rock")
        self.assertEqual(result_unusable, "Cannot use Rock.")
        self.assertEqual(len(player.inventory), 1)

        result_not_found = player.use_item("Imaginary Sword")
        self.assertEqual(result_not_found, "Item not found.")

    # Test attack_monster
    def test_player_attack_monster_no_weapon_monster_survives(self):
        player = Player(x=0, y=0, health=100)
        player.base_attack_power = 3

        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Goblin"
        # monster.take_damage returns a dict {'defeated': False/True}
        mock_monster.take_damage.return_value = {"defeated": False}

        expected_return = {
            "damage_dealt": 3,
            "monster_defeated": False,
            "monster_name": "Goblin",
        }
        actual_return = player.attack_monster(mock_monster)

        mock_monster.take_damage.assert_called_once_with(3)
        self.assertEqual(actual_return, expected_return)

    def test_player_attack_monster_with_weapon_monster_defeated(self):
        player = Player(x=0, y=0, health=100)
        player.base_attack_power = 3
        sword = Item(
            "Steel Sword", "A fine sword.", {"type": "weapon", "attack_bonus": 7}
        )
        player.take_item(sword)
        player.use_item("Steel Sword")  # Equip the sword

        mock_monster = MagicMock(spec=Monster)
        mock_monster.name = "Orc"
        mock_monster.take_damage.return_value = {
            "defeated": True
        }  # Monster is defeated

        expected_damage = (
            player.base_attack_power + sword.properties["attack_bonus"]
        )  # 3 + 7 = 10
        expected_return = {
            "damage_dealt": expected_damage,
            "monster_defeated": True,
            "monster_name": "Orc",
        }
        actual_return = player.attack_monster(mock_monster)

        mock_monster.take_damage.assert_called_once_with(expected_damage)
        self.assertEqual(actual_return, expected_return)

    # Test take_damage
    def test_player_take_damage_reduces_health_and_returns_dict(self):
        player = Player(x=0, y=0, health=100)

        result1 = player.take_damage(20)
        self.assertEqual(player.health, 80)
        self.assertEqual(result1, {"damage_taken": 20, "is_defeated": False})

        result2 = player.take_damage(30)
        self.assertEqual(player.health, 50)
        self.assertEqual(result2, {"damage_taken": 30, "is_defeated": False})

    def test_player_take_damage_health_not_below_zero_and_defeated_true(self):
        player = Player(x=0, y=0, health=10)

        result = player.take_damage(15)
        self.assertEqual(player.health, 0)
        self.assertEqual(result, {"damage_taken": 15, "is_defeated": True})

        # Taking more damage when already at 0
        result_more_damage = player.take_damage(5)
        self.assertEqual(player.health, 0)
        self.assertEqual(result_more_damage, {"damage_taken": 5, "is_defeated": True})

    def test_player_take_zero_damage(self):
        player = Player(x=0, y=0, health=75)
        result = player.take_damage(0)
        self.assertEqual(player.health, 75)
        self.assertEqual(result, {"damage_taken": 0, "is_defeated": False})


if __name__ == "__main__":
    unittest.main()

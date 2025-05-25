import unittest
from unittest.mock import MagicMock

from src.monster import Monster

# Player is only needed for type hinting in Monster, but we mock it for tests.
# from src.player import Player


class TestMonster(unittest.TestCase):
    def test_monster_initialization_default_coords(self):
        monster = Monster(name="Goblin", health=30, attack_power=5)
        self.assertEqual(monster.name, "Goblin")
        self.assertEqual(monster.health, 30)
        self.assertEqual(monster.attack_power, 5)
        self.assertEqual(monster.x, 0)
        self.assertEqual(monster.y, 0)

    def test_monster_initialization_custom_coords(self):
        monster = Monster(name="Orc", health=50, attack_power=10, x=5, y=10)
        self.assertEqual(monster.name, "Orc")
        self.assertEqual(monster.health, 50)
        self.assertEqual(monster.attack_power, 10)
        self.assertEqual(monster.x, 5)
        self.assertEqual(monster.y, 10)

    # Test take_damage Method
    def test_take_damage_reduces_health_and_returns_correct_dict(self):
        monster = Monster(name="Slime", health=20, attack_power=2)

        result1 = monster.take_damage(5)
        self.assertEqual(monster.health, 15)
        self.assertEqual(result1, {"damage_taken": 5, "defeated": False})

        result2 = monster.take_damage(10)
        self.assertEqual(monster.health, 5)
        self.assertEqual(result2, {"damage_taken": 10, "defeated": False})

    def test_take_damage_health_not_below_zero_and_defeated_true(self):
        monster = Monster(name="Zombie", health=10, attack_power=3)
        result = monster.take_damage(15)
        self.assertEqual(monster.health, 0)
        self.assertEqual(result, {"damage_taken": 15, "defeated": True})

    def test_take_damage_exact_kill(self):
        monster = Monster(name="Skeleton", health=10, attack_power=3)
        result = monster.take_damage(10)
        self.assertEqual(monster.health, 0)
        self.assertEqual(result, {"damage_taken": 10, "defeated": True})

    def test_take_damage_zero_damage(self):
        monster = Monster(name="Ghost", health=25, attack_power=4)
        result = monster.take_damage(0)
        self.assertEqual(monster.health, 25)
        self.assertEqual(result, {"damage_taken": 0, "defeated": False})

    # Test attack Method
    def test_attack_calls_player_take_damage_and_returns_correct_dict_player_survives(
        self,
    ):
        monster = Monster(name="Dragon", health=100, attack_power=20)

        # Mock the player object
        mock_player = MagicMock()
        # player.take_damage should return {'is_defeated': False/True}
        mock_player.take_damage.return_value = {"is_defeated": False}

        expected_return = {"damage_dealt_to_player": 20, "player_is_defeated": False}
        actual_return = monster.attack(mock_player)

        mock_player.take_damage.assert_called_once_with(20)  # Monster's attack power
        self.assertEqual(actual_return, expected_return)

    def test_attack_calls_player_take_damage_and_returns_correct_dict_player_defeated(
        self,
    ):
        monster = Monster(name="Lich", health=100, attack_power=75)

        mock_player = MagicMock()
        mock_player.take_damage.return_value = {
            "is_defeated": True
        }  # Player is defeated

        expected_return = {"damage_dealt_to_player": 75, "player_is_defeated": True}
        actual_return = monster.attack(mock_player)

        mock_player.take_damage.assert_called_once_with(75)
        self.assertEqual(actual_return, expected_return)


if __name__ == "__main__":
    unittest.main()

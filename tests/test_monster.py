import random
import unittest
from unittest.mock import MagicMock, patch

from src.monster import Monster

# Player is only needed for type hinting in Monster, but we mock it for tests.
# from src.player import Player


class TestMonster(unittest.TestCase):
    def setUp(self):
        self.random_generator = random.Random(12345)

    def test_monster_initialization_default_coords(self):
        monster = Monster(
            "Goblin",
            30,
            5,
            self.random_generator,
        )
        self.assertEqual(monster.name, "Goblin")
        self.assertEqual(monster.health, 30)
        self.assertEqual(monster.attack_power, 5)
        self.assertEqual(monster.x, 0)
        self.assertEqual(monster.y, 0)
        self.assertEqual(monster.move_speed, 1)
        self.assertEqual(monster.move_energy, 0)

    def test_monster_initialization_custom_coords(self):
        monster = Monster("Orc", 50, 10, self.random_generator, x=5, y=10)
        self.assertEqual(monster.name, "Orc")
        self.assertEqual(monster.health, 50)
        self.assertEqual(monster.attack_power, 10)
        self.assertEqual(monster.x, 5)
        self.assertEqual(monster.y, 10)

    def test_monster_initialization_with_move_speed(self):
        monster = Monster(
            "Goblin",
            10,
            3,
            self.random_generator,
            x=5,
            y=5,
            move_speed=5,
        )
        self.assertEqual(monster.move_speed, 5)
        self.assertEqual(monster.move_energy, 0)

    # Test take_damage Method
    def test_take_damage_reduces_health_and_returns_correct_dict(self):
        monster = Monster(
            "Slime",
            20,
            2,
            self.random_generator,
        )

        result1 = monster.take_damage(5)
        self.assertEqual(monster.health, 15)
        self.assertEqual(result1, {"damage_taken": 5, "defeated": False})

        result2 = monster.take_damage(10)
        self.assertEqual(monster.health, 5)
        self.assertEqual(result2, {"damage_taken": 10, "defeated": False})

    def test_take_damage_health_not_below_zero_and_defeated_true(self):
        monster = Monster(
            "Zombie",
            10,
            3,
            self.random_generator,
        )
        result = monster.take_damage(15)
        self.assertEqual(monster.health, 0)
        self.assertEqual(result, {"damage_taken": 15, "defeated": True})

    def test_take_damage_exact_kill(self):
        monster = Monster(
            "Skeleton",
            10,
            3,
            self.random_generator,
        )
        result = monster.take_damage(10)
        self.assertEqual(monster.health, 0)
        self.assertEqual(result, {"damage_taken": 10, "defeated": True})

    def test_take_damage_zero_damage(self):
        monster = Monster(
            "Ghost",
            25,
            4,
            self.random_generator,
        )
        result = monster.take_damage(0)
        self.assertEqual(monster.health, 25)
        self.assertEqual(result, {"damage_taken": 0, "defeated": False})

    # Test attack Method
    def test_attack_calls_player_take_damage_and_returns_correct_dict_player_survives(
        self,
    ):
        monster = Monster(
            "Dragon",
            100,
            20,
            self.random_generator,
        )

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
        monster = Monster(
            "Lich",
            100,
            75,
            self.random_generator,
        )

        mock_player = MagicMock()
        mock_player.take_damage.return_value = {
            "is_defeated": True
        }  # Player is defeated

        expected_return = {"damage_dealt_to_player": 75, "player_is_defeated": True}
        actual_return = monster.attack(mock_player)

        mock_player.take_damage.assert_called_once_with(75)
        self.assertEqual(actual_return, expected_return)

    def test_take_damage_with_defense(self):
        monster = Monster("Armored Golem", 50, 10, self.random_generator, defense=5)
        result = monster.take_damage(15)
        self.assertEqual(monster.health, 40)
        self.assertEqual(result["damage_taken"], 10)

    def test_take_damage_with_resistance(self):
        monster = Monster(
            "Fire Elemental",
            30,
            10,
            self.random_generator,
            resistance="fire",
        )
        result = monster.take_damage(20, "fire")
        self.assertEqual(monster.health, 20)
        self.assertEqual(result["damage_taken"], 10)

    def test_take_damage_with_vulnerability(self):
        monster = Monster(
            "Ice Golem",
            40,
            10,
            self.random_generator,
            vulnerability="fire",
        )
        result = monster.take_damage(10, "fire")
        self.assertEqual(monster.health, 20)
        self.assertEqual(result["damage_taken"], 20)

    def test_take_damage_with_evasion(self):
        monster = Monster("Rogue", 20, 5, self.random_generator, evasion=0.5)
        with patch.object(monster.random, "random", return_value=0.1):
            result = monster.take_damage(10)
            self.assertEqual(monster.health, 20)
            self.assertEqual(result["damage_taken"], 0)


if __name__ == "__main__":
    unittest.main()

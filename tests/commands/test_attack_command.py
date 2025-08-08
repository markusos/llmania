import random
import unittest
from unittest.mock import MagicMock

from src.commands.attack_command import AttackCommand
from src.monster import Monster
from src.player import Player
from src.world_map import WorldMap


class TestAttackCommand(unittest.TestCase):
    def setUp(self):
        self.player = MagicMock(spec=Player)
        self.world_map = MagicMock(spec=WorldMap)
        self.message_log = MagicMock()
        self.game_engine = MagicMock()
        self.random_generator = random.Random(9)

        # Common setup for player and monster
        self.player.health = 100
        self.player.get_attack_power.return_value = 10
        self.player.get_attack_speed.return_value = 5

        self.monster = Monster(
            name="Goblin",
            health=5,
            attack_power=1,
            x=5,
            y=6,
            attack_speed=1,
            random_generator=self.random_generator,
        )

        # Mock game engine's random generator
        self.game_engine.random = self.random_generator

    def test_monster_attacks_and_is_defeated_on_player_counter(self):
        """
        Tests that when a monster attacks a player and the player's
        counter-attack defeats it, the monster is correctly removed from the map.
        This covers the bug where monster_tile.x caused an AttributeError.
        """
        # Arrange
        # Monster attacks player, player survives
        self.monster.attack = MagicMock(
            return_value={"damage_dealt_to_player": 1, "player_is_defeated": False}
        )
        # Player counter-attacks and defeats monster
        self.player.attack_monster = MagicMock(
            return_value={"damage_dealt": 10, "monster_defeated": True}
        )

        # We need to control the hit chance calculation
        # First random call is for monster's attack, second for player's counter-attack
        # Let's assume both hit for this test.
        self.game_engine.random.random = MagicMock(return_value=0.0)

        command = AttackCommand(
            player=self.player,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=(0, 0, 0),
            game_engine=self.game_engine,
            entity=self.monster,
        )

        # Act
        result = command.execute()

        # Assert
        self.assertFalse(result["game_over"])

        # Check that monster's attack was called
        self.monster.attack.assert_called_once_with(self.player)

        # Check that player's counter-attack was called
        self.player.attack_monster.assert_called_once_with(self.monster)

        # This is the core of the bug fix: assert remove_monster was called
        # with the monster's own coordinates.
        self.world_map.remove_monster.assert_called_once_with(
            self.monster.x, self.monster.y
        )

        # Check that appropriate messages were logged
        self.message_log.add_message.assert_any_call(
            "The Goblin attacks you for 1 damage."
        )
        self.message_log.add_message.assert_any_call(
            "You attack the Goblin for 10 damage."
        )
        self.message_log.add_message.assert_any_call("You defeated the Goblin!")


if __name__ == "__main__":
    unittest.main()

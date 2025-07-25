import random
import unittest
from unittest.mock import mock_open, patch

from src.item_factory import ItemFactory
from src.monster_factory import MonsterFactory


class TestFactories(unittest.TestCase):
    def test_item_factory(self):
        item_data = """
        {
            "health_potion": {
                "name": "Health Potion",
                "description": "Restores some HP.",
                "properties": {
                    "type": "heal",
                    "amount": 10
                },
                "rarity": 70
            },
            "dagger": {
                "name": "Dagger",
                "description": "A small blade.",
                "properties": {
                    "type": "weapon",
                    "attack_bonus": 2,
                    "verb": "stabs",
                    "slot": "main_hand"
                },
                "rarity": 30
            }
        }
        """
        with patch("builtins.open", mock_open(read_data=item_data)):
            factory = ItemFactory("dummy/path/items.json")
            potion = factory.create_item("health_potion")
            self.assertIsNotNone(potion)
            assert potion is not None
            self.assertEqual(potion.name, "Health Potion")
            self.assertEqual(potion.properties["amount"], 10)

            dagger = factory.create_item("dagger")
            self.assertIsNotNone(dagger)
            assert dagger is not None
            self.assertEqual(dagger.name, "Dagger")
            from src.equippable import Equippable

            self.assertTrue(isinstance(dagger, Equippable))
            self.assertEqual(dagger.properties["attack_bonus"], 2)
            self.assertEqual(dagger.properties["slot"], "main_hand")

            random_item = factory.create_random_item(random.Random())
            self.assertIsNotNone(random_item)
            assert random_item is not None
            self.assertIn(random_item.name, ["Health Potion", "Dagger"])

    def test_monster_factory(self):
        monster_data = """
        {
            "goblin": {
                "name": "Goblin",
                "health": 10,
                "attack_power": 3,
                "rarity": 80,
                "move_speed": 2
            },
            "bat": {
                "name": "Bat",
                "health": 5,
                "attack_power": 2,
                "rarity": 20
            }
        }
        """
        with patch("builtins.open", mock_open(read_data=monster_data)):
            rng = random.Random()
            factory = MonsterFactory("dummy/path/monsters.json")
            goblin = factory.create_monster("goblin", random_generator=rng)
            self.assertIsNotNone(goblin)
            assert goblin is not None
            self.assertEqual(goblin.name, "Goblin")
            self.assertEqual(goblin.health, 10)
            self.assertEqual(goblin.attack_power, 3)
            self.assertEqual(goblin.move_speed, 2)

            bat = factory.create_monster("bat", random_generator=rng)
            self.assertIsNotNone(bat)
            assert bat is not None
            self.assertEqual(bat.name, "Bat")
            self.assertEqual(bat.health, 5)
            self.assertEqual(bat.attack_power, 2)

            random_monster = factory.create_random_monster(random_generator=rng)
            self.assertIsNotNone(random_monster)
            assert random_monster is not None
            self.assertIn(random_monster.name, ["Goblin", "Bat"])


if __name__ == "__main__":
    unittest.main()

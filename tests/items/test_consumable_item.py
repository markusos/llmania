import unittest
from unittest.mock import MagicMock, Mock

from src.items.consumable_item import ConsumableItem


class TestConsumableItem(unittest.TestCase):
    def test_init(self):
        effect1 = Mock()
        effect2 = Mock()
        item = ConsumableItem(
            "Health Potion",
            "A potion that heals",
            {},
            effects=[effect1, effect2],
        )
        self.assertEqual(item.name, "Health Potion")
        self.assertEqual(item.description, "A potion that heals")
        self.assertEqual(item.effects, [effect1, effect2])

    def test_apply(self):
        effect1 = MagicMock()
        effect1.apply.return_value = "Effect 1"
        effect2 = MagicMock()
        effect2.apply.return_value = "Effect 2"
        item = ConsumableItem(
            "Health Potion",
            "A potion that heals",
            {},
            effects=[effect1, effect2],
        )
        player = MagicMock()
        player.inventory = [item]
        game_engine = Mock()
        message = item.apply(player, game_engine)
        effect1.apply.assert_called_once_with(player, game_engine)
        effect2.apply.assert_called_once_with(player, game_engine)
        self.assertNotIn(item, player.inventory)
        self.assertEqual(message, "Effect 1 Effect 2")


if __name__ == "__main__":
    unittest.main()

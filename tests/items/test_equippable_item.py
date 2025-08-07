import unittest
from unittest.mock import MagicMock, Mock

from src.items.equippable import EquippableItem


class TestEquippableItem(unittest.TestCase):
    def test_init(self):
        properties = {
            "slot": "main_hand",
            "attack_bonus": 5,
            "defense_bonus": 2,
            "speed_bonus": 1,
            "max_health_bonus": 10,
        }
        item = EquippableItem("Sword", "A sharp sword", properties)
        self.assertEqual(item.name, "Sword")
        self.assertEqual(item.description, "A sharp sword")
        self.assertEqual(item.slot, "main_hand")
        self.assertEqual(item.attack_bonus, 5)
        self.assertEqual(item.defense_bonus, 2)
        self.assertEqual(item.speed_bonus, 1)
        self.assertEqual(item.max_health_bonus, 10)

    def test_apply(self):
        properties = {"slot": "main_hand", "attack_bonus": 5}
        item = EquippableItem("Sword", "A sharp sword", properties)
        player = MagicMock()
        game_engine = Mock()
        item.apply(player, game_engine)
        player.toggle_equip.assert_called_once_with(item)


if __name__ == "__main__":
    unittest.main()

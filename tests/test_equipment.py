import unittest

from src.equipment import Equipment
from src.items.equippable import EquippableItem


class TestEquipment(unittest.TestCase):
    def setUp(self):
        self.equipment = Equipment()
        self.weapon = EquippableItem(
            "weapon", "description", {"slot": "main_hand", "attack_bonus": 5}
        )
        self.armor = EquippableItem(
            "armor", "description", {"slot": "chest", "defense_bonus": 5}
        )

    def test_equip(self):
        self.equipment.equip(self.weapon, "main_hand")
        self.assertEqual(self.weapon, self.equipment.slots["main_hand"])

    def test_unequip(self):
        self.equipment.equip(self.weapon, "main_hand")
        unequipped_item = self.equipment.unequip("main_hand")
        self.assertEqual(self.weapon, unequipped_item)
        self.assertIsNone(self.equipment.slots["main_hand"])

    def test_get_total_bonus(self):
        self.equipment.equip(self.weapon, "main_hand")
        self.equipment.equip(self.armor, "chest")
        self.assertEqual(5, self.equipment.get_total_bonus("attack"))
        self.assertEqual(5, self.equipment.get_total_bonus("defense"))
        self.assertEqual(0, self.equipment.get_total_bonus("speed"))


if __name__ == "__main__":
    unittest.main()

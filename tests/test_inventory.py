import unittest

from src.inventory import Inventory
from src.items.consumable_item import ConsumableItem


class TestInventory(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()
        self.item1 = ConsumableItem("item1", "description1", {}, [])
        self.item2 = ConsumableItem("item2", "description2", {}, [])

    def test_add_item(self):
        self.inventory.add_item(self.item1)
        self.assertIn(self.item1, self.inventory.items)

    def test_remove_item(self):
        self.inventory.add_item(self.item1)
        self.inventory.remove_item(self.item1)
        self.assertNotIn(self.item1, self.inventory.items)

    def test_find_item(self):
        self.inventory.add_item(self.item1)
        found_item = self.inventory.find_item("item1")
        self.assertEqual(self.item1, found_item)

    def test_find_item_not_found(self):
        found_item = self.inventory.find_item("non_existent_item")
        self.assertIsNone(found_item)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.looting_state import LootingState


class TestLootingState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        self.state = LootingState(self.ai_logic)

    def test_handle_transitions(self):
        # Test transition to SurvivalState
        self.ai_logic.player.health = 1
        self.ai_logic.player.max_health = 10
        self.assertEqual(self.state.handle_transitions(), "SurvivalState")

        # Test transition to AttackingState
        self.ai_logic.player.health = 10
        self.ai_logic.player.max_health = 10
        self.ai_logic._get_adjacent_monsters.return_value = [MagicMock()]
        self.assertEqual(self.state.handle_transitions(), "AttackingState")

        # Test no transition
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.assertEqual(self.state.handle_transitions(), "LootingState")

    def test_get_next_action(self):
        # Test using a health potion
        item = MagicMock()
        item.properties = {"type": "heal"}
        item.name = "Health Potion"
        self.ai_logic.player.inventory = [item]
        self.ai_logic.player.health = 1
        self.ai_logic.player.max_health = 10
        action = self.state.get_next_action()
        self.assertEqual(action, ("use", "Health Potion"))

        # Test equipping a better weapon
        self.ai_logic.player.health = 10
        self.ai_logic.player.max_health = 10
        weapon1 = MagicMock()
        weapon1.properties = {"type": "weapon", "attack_bonus": 5}
        weapon1.name = "Sword"
        weapon2 = MagicMock()
        weapon2.properties = {"type": "weapon", "attack_bonus": 10}
        weapon2.name = "Axe"
        self.ai_logic.player.inventory = [weapon1, weapon2]
        self.ai_logic.player.equipped_weapon = weapon1
        action = self.state.get_next_action()
        self.assertEqual(action, ("use", "Axe"))

        # Test taking an item
        self.ai_logic.player.inventory = []
        (
            self.ai_logic.ai_visible_maps.get.return_value.get_tile.return_value.item.name
        ) = "Rock"
        action = self.state.get_next_action()
        self.assertEqual(action, ("take", "Rock"))

        # Test pathfinding to an item
        self.ai_logic.ai_visible_maps.get.return_value.get_tile.return_value.item = None
        self.ai_logic.target_finder.find_other_items.return_value = [
            (1, 1, 0, "item", 1)
        ]
        self.ai_logic.path_finder.find_path_bfs.return_value = [(1, 1, 0)]
        self.state._follow_path = MagicMock()
        self.state.get_next_action()
        self.state._follow_path.assert_called()

        # Test exploring
        self.ai_logic.target_finder.find_other_items.return_value = []
        self.state.get_next_action()
        self.ai_logic._get_state.assert_called_with("ExploringState")

        # Test that it doesn't path to an item on the same tile
        self.ai_logic.player.x = 1
        self.ai_logic.player.y = 1
        self.ai_logic.player.current_floor_id = 0
        self.ai_logic.target_finder.find_other_items.return_value = [
            (1, 1, 0, "item", 0)
        ]
        self.ai_logic.path_finder.find_path_bfs.reset_mock()
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_bfs.assert_not_called()

"""Tests for PickupItemAction."""

from unittest.mock import Mock

from src.ai_logic.actions.pickup_action import PickupItemAction
from src.ai_logic.context import AIContext


def create_mock_context(**kwargs):
    """Create a mock AIContext with default values."""
    defaults = {
        "player_x": 5,
        "player_y": 5,
        "player_floor_id": 0,
        "player_health": 100,
        "player_max_health": 100,
        "player_attack": 5,
        "player_defense": 2,
        "health_ratio": 1.0,
        "survival_threshold": 0.5,
        "is_cornered": False,
        "is_in_loop": False,
        "loop_breaker_active": False,
        "adjacent_monsters": [],
        "current_tile_has_item": False,
        "current_tile_item_name": None,
        "current_tile_item": None,
        "inventory_items": [],
        "has_healing_item": False,
        "has_fire_potion": False,
        "equipped_items": {},
        "current_path": None,
        "visible_maps": {},
        "path_finder": None,
        "bestiary": None,
        "explorer": None,
        "target_finder": None,
        "random": None,
    }
    defaults.update(kwargs)
    return AIContext(**defaults)  # type: ignore[arg-type]


class TestPickupItemAction:
    """Test suite for PickupItemAction."""

    def test_is_available_returns_true_when_item_on_tile(self):
        """Test is_available returns True when item on current tile."""
        action = PickupItemAction()
        ctx = create_mock_context(
            current_tile_has_item=True, current_tile_item_name="Health Potion"
        )
        assert action.is_available(ctx) is True

    def test_is_available_returns_false_when_no_item_on_tile(self):
        """Test is_available returns False when no item on tile."""
        action = PickupItemAction()
        ctx = create_mock_context(
            current_tile_has_item=False, current_tile_item_name=None
        )
        assert action.is_available(ctx) is False

    def test_calculate_utility_returns_0_80_for_regular_item(self):
        """Test calculate_utility returns 0.80 for regular items."""
        action = PickupItemAction()
        ctx = create_mock_context(
            current_tile_has_item=True,
            current_tile_item_name="Gold Coin",
            current_tile_item=None,  # Not a quest item
        )
        assert action.calculate_utility(ctx) == 0.80

    def test_calculate_utility_returns_0_99_for_quest_item(self):
        """Test calculate_utility returns 0.99 for quest items (winning priority)."""
        from src.items import QuestItem

        quest_item = QuestItem("Ancient Artifact", "Win the game!", {})
        action = PickupItemAction()
        ctx = create_mock_context(
            current_tile_has_item=True,
            current_tile_item_name="Ancient Artifact",
            current_tile_item=quest_item,
        )
        assert action.calculate_utility(ctx) == 0.99

    def test_execute_returns_take_command(self):
        """Test execute returns ('take', item_name)."""
        action = PickupItemAction()
        ctx = create_mock_context(
            current_tile_has_item=True, current_tile_item_name="Iron Sword"
        )
        ai_logic = Mock()
        message_log = Mock()

        result = action.execute(ctx, ai_logic, message_log)
        assert result == ("take", "Iron Sword")
        assert ai_logic.current_path is None
        message_log.add_message.assert_called()

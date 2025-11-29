"""Tests for HealAction."""

from unittest.mock import Mock

from src.ai_logic.actions.heal_action import HealAction
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
    return AIContext(**defaults)


class TestHealAction:
    """Test suite for HealAction."""

    def test_is_available_returns_false_when_no_healing_item(self):
        """Test is_available returns False when no healing item."""
        action = HealAction()
        ctx = create_mock_context(
            has_healing_item=False, player_health=50, player_max_health=100
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_false_when_health_is_full(self):
        """Test is_available returns False when health is full."""
        action = HealAction()
        ctx = create_mock_context(
            has_healing_item=True, player_health=100, player_max_health=100
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_has_healing_and_low_health(self):
        """Test is_available returns True when has healing and health < max."""
        action = HealAction()
        ctx = create_mock_context(
            has_healing_item=True, player_health=50, player_max_health=100
        )
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_1_when_health_below_threshold(self):
        """Test calculate_utility returns 1.0 when health <= survival_threshold."""
        action = HealAction()
        ctx = create_mock_context(
            has_healing_item=True,
            player_health=40,
            player_max_health=100,
            health_ratio=0.4,
            survival_threshold=0.5,
        )
        assert action.calculate_utility(ctx) == 1.0

    def test_calculate_utility_returns_0_98_when_adjacent_monster_critical(self):
        """Test utility 0.98 when adjacent monster and health <= incoming*1.5."""
        from src.ai_logic.ai_monster_view import AIMonsterView

        # Create mock bestiary
        mock_bestiary = Mock()
        mock_bestiary.get_attack_power.return_value = 10
        mock_bestiary.get_danger_rating.return_value = 2

        action = HealAction()
        ctx = create_mock_context(
            has_healing_item=True,
            player_health=15,  # <= 10 * 1.5
            player_max_health=100,
            health_ratio=0.15,
            survival_threshold=0.1,  # Not triggering 1.0 utility
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            bestiary=mock_bestiary,
        )
        assert action.calculate_utility(ctx) == 0.98

    def test_calculate_utility_returns_0_96_when_half_health_danger_monster(self):
        """Test utility 0.96 when health <= 50% and facing danger >= 3."""
        from src.ai_logic.ai_monster_view import AIMonsterView

        # Create mock bestiary with high danger monster
        mock_bestiary = Mock()
        mock_bestiary.get_attack_power.return_value = 5
        mock_bestiary.get_danger_rating.return_value = 3

        action = HealAction()
        ctx = create_mock_context(
            has_healing_item=True,
            player_health=50,
            player_max_health=100,
            health_ratio=0.5,
            survival_threshold=0.3,  # Not triggering 1.0 utility
            adjacent_monsters=[AIMonsterView("Troll", 4, 5)],
            bestiary=mock_bestiary,
        )
        assert action.calculate_utility(ctx) == 0.96

    def test_calculate_utility_returns_0_when_healthy_no_monsters(self):
        """Test calculate_utility returns 0.0 when healthy and no threats."""
        action = HealAction()
        ctx = create_mock_context(
            has_healing_item=True,
            player_health=90,
            player_max_health=100,
            health_ratio=0.9,
            survival_threshold=0.5,
        )
        assert action.calculate_utility(ctx) == 0.0

    def test_execute_returns_use_command_for_healing_item(self):
        """Test execute returns ('use', item_name) for first healing item."""
        # Create mock healing item
        mock_item = Mock()
        mock_item.name = "Health Potion"
        mock_item.properties = {"type": "heal"}

        action = HealAction()
        ctx = create_mock_context(
            inventory_items=[mock_item], has_healing_item=True, player_health=50
        )
        ai_logic = Mock()
        message_log = Mock()

        result = action.execute(ctx, ai_logic, message_log)
        assert result == ("use", "Health Potion")
        message_log.add_message.assert_called()

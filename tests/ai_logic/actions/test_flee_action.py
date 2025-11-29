"""Tests for FleeAction."""

from unittest.mock import Mock

from src.ai_logic.actions.flee_action import FleeAction
from src.ai_logic.ai_monster_view import AIMonsterView
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


class TestFleeAction:
    """Test suite for FleeAction."""

    def test_is_available_returns_false_when_no_adjacent_monsters(self):
        """Test is_available returns False when no adjacent monsters."""
        action = FleeAction()
        ctx = create_mock_context(
            adjacent_monsters=[],
            is_cornered=False,
            health_ratio=0.3,
            survival_threshold=0.5,
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_false_when_cornered(self):
        """Test is_available returns False when cornered."""
        action = FleeAction()
        ctx = create_mock_context(
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            is_cornered=True,
            health_ratio=0.3,
            survival_threshold=0.5,
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_false_when_healthy(self):
        """Test is_available returns False when health is not low."""
        action = FleeAction()
        ctx = create_mock_context(
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            is_cornered=False,
            health_ratio=0.8,
            survival_threshold=0.5,
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_can_flee(self):
        """Test is_available returns True when has safe escape route."""
        action = FleeAction()
        ctx = create_mock_context(
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            is_cornered=False,
            health_ratio=0.3,
            survival_threshold=0.5,
        )
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_0_95_when_low_health_and_can_flee(self):
        """Test calculate_utility returns 0.95 when low health and can flee."""
        action = FleeAction()
        ctx = create_mock_context(
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            is_cornered=False,
            health_ratio=0.3,
            survival_threshold=0.5,
        )
        assert action.calculate_utility(ctx) == 0.95

    def test_calculate_utility_returns_0_when_healthy(self):
        """Test calculate_utility returns 0.0 when healthy."""
        action = FleeAction()
        ctx = create_mock_context(
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            is_cornered=False,
            health_ratio=0.8,
            survival_threshold=0.5,
        )
        assert action.calculate_utility(ctx) == 0.0

    def test_calculate_utility_returns_0_when_no_monsters(self):
        """Test calculate_utility returns 0.0 when no adjacent monsters."""
        action = FleeAction()
        ctx = create_mock_context(
            adjacent_monsters=[],
            is_cornered=False,
            health_ratio=0.3,
            survival_threshold=0.5,
        )
        assert action.calculate_utility(ctx) == 0.0

    def test_execute_returns_move_command(self):
        """Test execute returns a move command away from threat."""
        action = FleeAction()

        # Create mock map with safe tiles
        mock_tile = Mock()
        mock_tile.type = "floor"
        mock_tile.monster = None

        mock_map = Mock()
        mock_map.get_tile.return_value = mock_tile

        mock_random = Mock()
        mock_random.choice.side_effect = lambda x: x[0]

        ctx = create_mock_context(
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],  # West of player
            is_cornered=False,
            health_ratio=0.3,
            survival_threshold=0.5,
            visible_maps={0: mock_map},
            random=mock_random,
        )

        mock_ai_logic = Mock()
        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)

        assert result is not None
        assert result[0] == "move"
        assert result[1] in ["north", "south", "east", "west"]

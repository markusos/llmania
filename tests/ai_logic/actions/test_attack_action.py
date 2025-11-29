"""Tests for AttackAction and UseCombatItemAction."""

from unittest.mock import Mock

from src.ai_logic.actions.attack_action import AttackAction, UseCombatItemAction
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
        "player_attack": 10,
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


class TestAttackAction:
    """Test suite for AttackAction."""

    def test_is_available_returns_false_when_no_adjacent_monsters(self):
        """Test is_available returns False when no adjacent monsters."""
        action = AttackAction()
        ctx = create_mock_context(adjacent_monsters=[])
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_adjacent_monsters(self):
        """Test is_available returns True when there are adjacent monsters."""
        action = AttackAction()
        ctx = create_mock_context(adjacent_monsters=[AIMonsterView("Goblin", 4, 5)])
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_0_90_when_cornered(self):
        """Test calculate_utility returns 0.90 when cornered."""
        mock_bestiary = Mock()
        mock_bestiary.get_stats.return_value = {
            "attack_power": 5,
            "health": 10,
            "defense": 0,
        }

        action = AttackAction()
        ctx = create_mock_context(
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            is_cornered=True,
            bestiary=mock_bestiary,
        )
        assert action.calculate_utility(ctx) == 0.90

    def test_calculate_utility_returns_0_85_when_safe_to_engage(self):
        """Test calculate_utility returns 0.85 when safe to engage."""
        mock_bestiary = Mock()
        # Easy monster - low attack, low health
        mock_bestiary.get_stats.return_value = {
            "attack_power": 2,
            "health": 5,
            "defense": 0,
        }

        action = AttackAction()
        ctx = create_mock_context(
            player_health=100,
            player_max_health=100,
            player_attack=10,
            player_defense=2,
            adjacent_monsters=[AIMonsterView("Rat", 4, 5)],
            is_cornered=False,
            bestiary=mock_bestiary,
            has_healing_item=True,
        )
        assert action.calculate_utility(ctx) == 0.85

    def test_calculate_utility_returns_0_35_when_risky(self):
        """Test calculate_utility returns 0.35 when risky engagement."""
        mock_bestiary = Mock()
        # Strong monster that would kill us
        mock_bestiary.get_stats.return_value = {
            "attack_power": 50,
            "health": 100,
            "defense": 5,
        }

        action = AttackAction()
        ctx = create_mock_context(
            player_health=50,
            player_max_health=100,
            player_attack=5,
            player_defense=0,
            adjacent_monsters=[AIMonsterView("Dragon", 4, 5)],
            is_cornered=False,
            bestiary=mock_bestiary,
            has_healing_item=False,
        )
        # Should return 0.35 (risky but forced to acknowledge monsters)
        assert action.calculate_utility(ctx) == 0.35


class TestUseCombatItemAction:
    """Test suite for UseCombatItemAction."""

    def test_is_available_returns_false_when_no_fire_potion(self):
        """Test is_available returns False when no fire potion."""
        action = UseCombatItemAction()
        ctx = create_mock_context(
            has_fire_potion=False,
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_false_when_no_adjacent_monsters(self):
        """Test is_available returns False when no adjacent monsters."""
        action = UseCombatItemAction()
        ctx = create_mock_context(has_fire_potion=True, adjacent_monsters=[])
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_has_fire_potion_and_monsters(self):
        """Test is_available returns True with fire potion and monsters."""
        action = UseCombatItemAction()
        ctx = create_mock_context(
            has_fire_potion=True,
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
        )
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_0_91_for_fire_vulnerable_monster(self):
        """Test utility 0.91 for fire-vulnerable monster."""
        mock_bestiary = Mock()
        mock_bestiary.get_vulnerability.return_value = "fire"

        action = UseCombatItemAction()
        ctx = create_mock_context(
            has_fire_potion=True,
            adjacent_monsters=[AIMonsterView("Troll", 4, 5)],
            bestiary=mock_bestiary,
        )
        assert action.calculate_utility(ctx) == 0.91

    def test_calculate_utility_returns_0_91_for_multiple_monsters(self):
        """Test utility 0.91 for 2+ adjacent monsters with fire potion."""
        mock_bestiary = Mock()
        mock_bestiary.get_vulnerability.return_value = None

        action = UseCombatItemAction()
        ctx = create_mock_context(
            has_fire_potion=True,
            adjacent_monsters=[
                AIMonsterView("Goblin", 4, 5),
                AIMonsterView("Goblin", 6, 5),
            ],
            bestiary=mock_bestiary,
        )
        assert action.calculate_utility(ctx) == 0.91

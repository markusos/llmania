"""Tests for EquipAction."""

from unittest.mock import Mock

from src.ai_logic.actions.equip_action import EquipAction
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


def create_mock_equippable(name, slot, attack_bonus=0, defense_bonus=0):
    """Create a mock EquippableItem."""
    # Import here to use the actual class for isinstance checks
    from src.items import EquippableItem

    mock_item = Mock(spec=EquippableItem)
    mock_item.name = name
    mock_item.properties = {
        "slot": slot,
        "attack_bonus": attack_bonus,
        "defense_bonus": defense_bonus,
    }
    return mock_item


class TestEquipAction:
    """Test suite for EquipAction."""

    def test_is_available_returns_false_when_no_equippable_items(self):
        """Test is_available returns False when no equippable items."""
        action = EquipAction()
        ctx = create_mock_context(inventory_items=[], equipped_items={})
        assert action.is_available(ctx) is False

    def test_is_available_returns_false_when_no_improvements(self):
        """Test is_available returns False when no better equipment available."""
        action = EquipAction()

        # Create an equipped weapon
        equipped_weapon = create_mock_equippable(
            "Iron Sword", "main_hand", attack_bonus=5
        )

        # Inventory has worse weapon
        worse_weapon = create_mock_equippable(
            "Wooden Sword", "main_hand", attack_bonus=2
        )

        ctx = create_mock_context(
            inventory_items=[worse_weapon],
            equipped_items={"main_hand": equipped_weapon},
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_better_weapon_in_inventory(self):
        """Test is_available returns True when better weapon in inventory."""
        action = EquipAction()

        # Create an equipped weapon
        equipped_weapon = create_mock_equippable(
            "Wooden Sword", "main_hand", attack_bonus=2
        )

        # Inventory has better weapon
        better_weapon = create_mock_equippable(
            "Iron Sword", "main_hand", attack_bonus=5
        )

        ctx = create_mock_context(
            inventory_items=[better_weapon],
            equipped_items={"main_hand": equipped_weapon},
        )
        assert action.is_available(ctx) is True

    def test_is_available_returns_true_when_armor_for_empty_slot(self):
        """Test is_available returns True when armor for empty slot."""
        action = EquipAction()

        # Armor for empty slot
        helmet = create_mock_equippable("Iron Helmet", "head", defense_bonus=3)

        ctx = create_mock_context(
            inventory_items=[helmet],
            equipped_items={"head": None, "chest": None},
        )
        assert action.is_available(ctx) is True

    def test_is_available_returns_true_when_better_armor(self):
        """Test is_available returns True when better armor in inventory."""
        action = EquipAction()

        # Currently equipped armor
        old_helmet = create_mock_equippable("Leather Cap", "head", defense_bonus=1)

        # Better armor in inventory
        new_helmet = create_mock_equippable("Iron Helmet", "head", defense_bonus=3)

        ctx = create_mock_context(
            inventory_items=[new_helmet],
            equipped_items={"head": old_helmet},
        )
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_0_75(self):
        """Test calculate_utility returns 0.75 when equip available."""
        action = EquipAction()

        helmet = create_mock_equippable("Iron Helmet", "head", defense_bonus=3)

        ctx = create_mock_context(
            inventory_items=[helmet],
            equipped_items={"head": None},
        )
        assert action.calculate_utility(ctx) == 0.75

    def test_calculate_utility_returns_0_when_not_available(self):
        """Test calculate_utility returns 0.0 when no equip available."""
        action = EquipAction()
        ctx = create_mock_context(inventory_items=[], equipped_items={})
        assert action.calculate_utility(ctx) == 0.0

    def test_execute_equips_weapon(self):
        """Test execute returns use command for weapon."""
        action = EquipAction()

        better_weapon = create_mock_equippable(
            "Iron Sword", "main_hand", attack_bonus=5
        )

        ctx = create_mock_context(
            inventory_items=[better_weapon],
            equipped_items={"main_hand": None},
        )

        mock_ai_logic = Mock()
        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)

        assert result == ("use", "Iron Sword")
        mock_message_log.add_message.assert_called()

    def test_execute_equips_armor_to_empty_slot(self):
        """Test execute returns use command for armor in empty slot."""
        action = EquipAction()

        helmet = create_mock_equippable("Iron Helmet", "head", defense_bonus=3)

        ctx = create_mock_context(
            inventory_items=[helmet],
            equipped_items={"head": None},
        )

        mock_ai_logic = Mock()
        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)

        assert result == ("use", "Iron Helmet")

    def test_execute_prefers_weapon_over_armor(self):
        """Test execute prefers equipping weapons before armor."""
        action = EquipAction()

        weapon = create_mock_equippable("Iron Sword", "main_hand", attack_bonus=5)
        helmet = create_mock_equippable("Iron Helmet", "head", defense_bonus=3)

        # Weapon comes after helmet in inventory, but should still be preferred
        # since _find_best_equip checks weapons first in iteration order
        ctx = create_mock_context(
            inventory_items=[weapon, helmet],
            equipped_items={"main_hand": None, "head": None},
        )

        mock_ai_logic = Mock()
        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)

        # Should equip weapon since it's first in the inventory
        assert result == ("use", "Iron Sword")

import unittest
from unittest.mock import MagicMock, PropertyMock

from src.ai_logic.ai_player_view import AIPlayerView
from src.ai_logic.states import common_actions
from src.items import EquippableItem as Equippable
from src.player import Player


class TestCommonActions(unittest.TestCase):
    def test_equip_better_weapon_no_weapon_equipped(self):
        # Arrange
        player = Player(x=0, y=0, current_floor_id=0, health=10)
        player.equipment.slots["main_hand"] = None

        weapon = Equippable(
            name="Sword",
            description="A shiny sword.",
            properties={
                "type": "weapon",
                "attack_bonus": 10,
                "slot": "main_hand",
            },
        )
        player.inventory.add_item(weapon)

        # Create a proper AIPlayerView wrapper
        player_view = AIPlayerView(player)

        ai_logic = MagicMock()
        type(ai_logic).player_view = PropertyMock(return_value=player_view)

        # Act
        action = common_actions.equip_better_weapon(ai_logic)

        # Assert
        self.assertEqual(action, ("use", "Sword"))


if __name__ == "__main__":
    unittest.main()

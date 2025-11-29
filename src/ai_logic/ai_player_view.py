"""Read-only view of player state visible to the AI."""

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.items import Item
    from src.player import Player


class AIPlayerView:
    """
    Read-only view of player state visible to the AI.

    This wrapper ensures the AI can only access information
    that a real player would know about themselves.
    """

    def __init__(self, player: "Player"):
        self._player = player

    # Position (always visible to player)
    @property
    def x(self) -> int:
        return self._player.x

    @property
    def y(self) -> int:
        return self._player.y

    @property
    def current_floor_id(self) -> int:
        return self._player.current_floor_id

    # Health (player knows their own health)
    @property
    def health(self) -> int:
        return self._player.health

    @property
    def max_health(self) -> int:
        return self._player.max_health

    # Combat stats (player knows their stats)
    def get_attack_power(self) -> int:
        return self._player.get_attack_power()

    def get_defense(self) -> int:
        return self._player.get_defense()

    # Inventory (player can see their inventory)
    @property
    def inventory_items(self) -> List["Item"]:
        return self._player.inventory.items

    # Equipment (player can see what they have equipped)
    def get_equipped_item(self, slot: str) -> Optional["Item"]:
        return self._player.equipment.slots.get(slot)

    def has_item_type(self, item_type: str) -> bool:
        """Check if player has an item of a specific type in inventory."""
        return any(
            item.properties.get("type") == item_type
            for item in self._player.inventory.items
        )

    def find_items_by_type(self, item_type: str) -> List["Item"]:
        """Find all items of a specific type in inventory."""
        return [
            item
            for item in self._player.inventory.items
            if item.properties.get("type") == item_type
        ]

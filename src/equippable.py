from src.item import Item


class Equippable(Item):
    """
    Represents an equippable item in the game.

    Attributes:
        slot (str): The equipment slot the item belongs to (e.g., "head",
            "chest", "main_hand").
        attack_bonus (int): The bonus to attack power when equipped.
    """

    def __init__(self, name: str, description: str, properties: dict):
        """
        Initializes an Equippable instance.

        Args:
            name: The name of the item.
            description: A textual description of the item.
            properties: A dictionary defining the item's characteristics and effects.
        """
        super().__init__(name, description, properties)
        self.slot = properties.get("slot")
        self.attack_bonus = properties.get("attack_bonus", 0)

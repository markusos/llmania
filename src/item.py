class Item:
    """
    Represents an item in the game, such as a weapon, potion, or quest object.

    Attributes:
        name (str): The display name of the item.
        description (str): A short description of the item.
        properties (dict): A dictionary containing item-specific properties,
                           e.g., {"type": "weapon", "attack_bonus": 5} or
                           {"type": "heal", "amount": 10}.
    """

    def __init__(self, name: str, description: str, properties: dict):
        """
        Initializes an Item instance.

        Args:
            name: The name of the item.
            description: A textual description of the item.
            properties: A dictionary defining the item's characteristics and effects.
                        Common keys include:
                        - "type": (str) e.g., "weapon", "heal", "quest", "junk",
                                    "cursed"
                        - "attack_bonus": (int) For weapons, the bonus to attack power.
                        - "verb": (str) For weapons, the verb used in attack messages
                                    (e.g., "stabs").
                        - "amount": (int) For healing items, the amount of health
                                    restored.
                        - "damage": (int) For cursed items, the amount of damage
                                    inflicted.
        """
        self.name = name
        self.description = description
        self.properties = properties

from item import Item


def test_item_initialization_health_potion():
    item_name = "Health Potion"
    item_description = "Restores 10 HP."
    item_properties = {"type": "heal", "amount": 10}

    potion = Item(
        name=item_name, description=item_description, properties=item_properties
    )

    assert potion.name == item_name
    assert potion.description == item_description
    assert potion.properties == item_properties
    assert potion.properties["type"] == "heal"
    assert potion.properties["amount"] == 10


def test_item_initialization_iron_sword():
    item_name = "Iron Sword"
    item_description = "A basic sword."
    item_properties = {"type": "weapon", "attack_bonus": 5, "verb": "slashes"}

    sword = Item(
        name=item_name, description=item_description, properties=item_properties
    )

    assert sword.name == item_name
    assert sword.description == item_description
    assert sword.properties == item_properties
    assert sword.properties["type"] == "weapon"
    assert sword.properties["attack_bonus"] == 5
    assert sword.properties["verb"] == "slashes"


def test_item_initialization_empty_properties():
    item_name = "Mysterious Orb"
    item_description = "Its purpose is unknown."
    item_properties = {}

    orb = Item(name=item_name, description=item_description, properties=item_properties)

    assert orb.name == item_name
    assert orb.description == item_description
    assert orb.properties == item_properties
    assert len(orb.properties) == 0

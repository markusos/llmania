from src.item import Item
from src.monster import Monster
from src.player import Player


# Test Initialization
def test_player_initialization():
    player = Player(x=1, y=2, health=100)
    assert player.x == 1
    assert player.y == 2
    assert player.health == 100
    assert player.inventory == []
    assert player.base_attack_power == 2  # Default value
    assert player.equipped_weapon is None


# Test move
def test_player_move():
    player = Player(x=5, y=5, health=100)
    player.move(1, -1)
    assert player.x == 6
    assert player.y == 4
    player.move(-2, 3)
    assert player.x == 4
    assert player.y == 7


# Test take_item
def test_player_take_item():
    player = Player(x=0, y=0, health=50)
    potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
    player.take_item(potion)
    assert len(player.inventory) == 1
    assert player.inventory[0] == potion
    assert player.inventory[0].name == "Potion"


# Test drop_item
def test_player_drop_item_found():
    player = Player(x=0, y=0, health=50)
    potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
    sword = Item("Sword", "A sharp blade", {"type": "weapon", "attack_bonus": 5})
    player.take_item(potion)
    player.take_item(sword)

    dropped_item = player.drop_item("Potion")
    assert dropped_item is not None
    assert dropped_item.name == "Potion"
    assert len(player.inventory) == 1
    assert player.inventory[0].name == "Sword"

    dropped_item_2 = player.drop_item("Sword")
    assert dropped_item_2 is not None
    assert dropped_item_2.name == "Sword"
    assert len(player.inventory) == 0


def test_player_drop_item_not_found():
    player = Player(x=0, y=0, health=50)
    potion = Item("Potion", "Heals", {"type": "heal", "amount": 10})
    player.take_item(potion)

    dropped_item = player.drop_item("NonExistentItem")
    assert dropped_item is None
    assert len(player.inventory) == 1  # Inventory unchanged


# Test use_item
def test_player_use_item_heal():
    player = Player(x=0, y=0, health=50)
    potion = Item("Health Potion", "Restores 10 HP.", {"type": "heal", "amount": 10})
    player.take_item(potion)

    result = player.use_item("Health Potion")
    assert player.health == 60
    assert len(player.inventory) == 0
    assert result == "Used Health Potion, healed by 10 HP."


def test_player_use_item_heal_full_health_still_consumes():
    player = Player(x=0, y=0, health=100)  # Assuming max health is high
    potion = Item("Health Potion", "Restores 10 HP.", {"type": "heal", "amount": 10})
    player.take_item(potion)

    result = player.use_item("Health Potion")
    assert player.health == 110  # Health can go above initial if not capped
    assert len(player.inventory) == 0
    assert result == "Used Health Potion, healed by 10 HP."


def test_player_use_item_weapon():
    player = Player(x=0, y=0, health=100)
    sword = Item("Iron Sword", "A basic sword.", {"type": "weapon", "attack_bonus": 5})
    player.take_item(sword)

    result = player.use_item("Iron Sword")
    assert player.equipped_weapon == sword
    assert player.equipped_weapon.name == "Iron Sword"
    assert len(player.inventory) == 1  # Weapon stays in inventory
    assert result == "Equipped Iron Sword."


def test_player_use_item_unusable():
    player = Player(x=0, y=0, health=100)
    rock = Item("Rock", "Just a rock.", {"type": "junk"})
    player.take_item(rock)

    result = player.use_item("Rock")
    assert player.health == 100
    assert player.equipped_weapon is None
    assert len(player.inventory) == 1  # Item remains
    assert result == "Cannot use Rock."


def test_player_use_item_not_found():
    player = Player(x=0, y=0, health=100)
    result = player.use_item("Imaginary Sword")
    assert result == "Item not found."
    assert player.health == 100
    assert player.equipped_weapon is None


# Test attack_monster
def test_player_attack_monster_no_weapon():
    player = Player(x=0, y=0, health=100)
    player.base_attack_power = 3  # Set for clarity
    monster = Monster("Goblin", health=20, attack_power=5)

    initial_monster_health = monster.health
    damage_dealt = player.attack_monster(monster)

    assert damage_dealt == 3
    assert monster.health == initial_monster_health - 3


def test_player_attack_monster_with_weapon():
    player = Player(x=0, y=0, health=100)
    player.base_attack_power = 3
    sword = Item("Steel Sword", "A fine sword.", {"type": "weapon", "attack_bonus": 7})
    player.take_item(sword)
    player.use_item("Steel Sword")  # Equip the sword

    monster = Monster("Orc", health=40, attack_power=10)

    initial_monster_health = monster.health
    expected_damage = player.base_attack_power + sword.properties["attack_bonus"]
    damage_dealt = player.attack_monster(monster)

    assert damage_dealt == expected_damage  # 3 + 7 = 10
    assert monster.health == initial_monster_health - expected_damage


# Test take_damage
def test_player_take_damage_reduces_health():
    player = Player(x=0, y=0, health=100)
    player.take_damage(20)
    assert player.health == 80
    player.take_damage(30)
    assert player.health == 50


def test_player_take_damage_health_not_below_zero():
    player = Player(x=0, y=0, health=10)
    player.take_damage(15)
    assert player.health == 0
    player.take_damage(5)  # Taking more damage when already at 0
    assert player.health == 0


def test_player_take_zero_damage():
    player = Player(x=0, y=0, health=75)
    player.take_damage(0)
    assert player.health == 75

from src.monster import Monster


# Test Initialization
def test_monster_initialization_default_coords():
    monster = Monster(name="Goblin", health=30, attack_power=5)
    assert monster.name == "Goblin"
    assert monster.health == 30
    assert monster.attack_power == 5
    assert monster.x == 0
    assert monster.y == 0


def test_monster_initialization_custom_coords():
    monster = Monster(name="Orc", health=50, attack_power=10, x=5, y=10)
    assert monster.name == "Orc"
    assert monster.health == 50
    assert monster.attack_power == 10
    assert monster.x == 5
    assert monster.y == 10


# Test take_damage Method
def test_take_damage_reduces_health():
    monster = Monster(name="Slime", health=20, attack_power=2)
    monster.take_damage(5)
    assert monster.health == 15
    monster.take_damage(10)
    assert monster.health == 5


def test_take_damage_health_not_below_zero():
    monster = Monster(name="Zombie", health=10, attack_power=3)
    monster.take_damage(15)
    assert monster.health == 0


def test_take_damage_zero_damage():
    monster = Monster(name="Ghost", health=25, attack_power=4)
    monster.take_damage(0)
    assert monster.health == 25


# Test attack Method
def test_attack_returns_attack_power():
    monster = Monster(name="Dragon", health=100, attack_power=20)
    # Passing None as player, as it's not used yet
    # Create a dummy player object that has a take_damage method
    class DummyPlayerForAttack: # Fixed indentation
        def __init__(self):
            self.health = 100
        def take_damage(self, amount):
            self.health -= amount
    dummy_player = DummyPlayerForAttack() # Fixed indentation
    assert monster.attack(dummy_player) == 20


def test_attack_with_dummy_player_object():
    monster = Monster(name="Skeleton", health=40, attack_power=8)

    class DummyPlayer:
        pass

    player_placeholder = DummyPlayer()
    # Ensure DummyPlayer has take_damage if monster.attack calls it
    # For this test, if Monster.attack truly needs a player with methods,
    # the dummy should have them. The current Monster.attack does.
    def take_damage_mock(amount): # Fixed indentation
        pass # Mock implementation
    player_placeholder.take_damage = take_damage_mock # Fixed indentation
    assert monster.attack(player_placeholder) == 8

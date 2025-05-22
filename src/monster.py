class Monster:
    def __init__(
        self, name: str, health: int, attack_power: int, x: int = 0, y: int = 0
    ):
        self.name = name
        self.health = health
        self.attack_power = attack_power
        self.x = x
        self.y = y

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def attack(
        self, player_to_attack
    ) -> int:  # player_to_attack is Player type, but forward ref
        player_to_attack.take_damage(self.attack_power)
        return self.attack_power

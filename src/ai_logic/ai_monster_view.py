"""View of monster that only exposes visible information."""


class AIMonsterView:
    """
    View of monster that only exposes visible information.

    This wrapper ensures the AI can only access information
    that a real player would see about a monster (name and position).
    Internal stats like health, attack_power, defense are NOT exposed.
    """

    def __init__(self, monster_name: str, x: int, y: int):
        self.name = monster_name  # Only the name is visible
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"AIMonsterView(name={self.name!r}, x={self.x}, y={self.y})"

    # No access to: health, attack_power, defense, evasion, etc.
    # Use Bestiary.get_stats(monster.name) to look up stats

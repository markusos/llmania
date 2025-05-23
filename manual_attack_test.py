import curses
from unittest.mock import patch

from src.game_engine import GameEngine
from src.monster import Monster
from src.world_generator import WorldGenerator  # Needed for GameEngine init
from src.world_map import WorldMap


def main():
    # Mock curses for GameEngine initialization
    with patch("src.game_engine.curses") as mock_curses:
        mock_curses.KEY_ENTER = curses.KEY_ENTER
        mock_curses.KEY_BACKSPACE = curses.KEY_BACKSPACE
        mock_curses.error = curses.error
        mock_curses.LINES = 24  # Mock LINES
        mock_curses.COLS = 80  # Mock COLS

        # Mock WorldGenerator to control map generation for simplicity
        # This setup is similar to the test fixtures
        with patch.object(
            WorldGenerator,
            "generate_map",
            return_value=(WorldMap(5, 5), (2, 2), (4, 4)),
        ):
            engine = GameEngine(map_width=5, map_height=5)

    # Override player and map for specific test scenario if generate_map mock isn't enough
    # engine.world_map = WorldMap(5, 5) # Ensure a fresh map if needed
    # engine.player = Player(x=2, y=2, health=20)
    # engine.world_map.get_tile(2,2).type = "floor" # Ensure player's tile is floor

    # Ensure player is at the desired start position from the mocked generate_map
    engine.player.x = 2
    engine.player.y = 2
    engine.player.health = 20
    engine.player.base_attack_power = 5  # Give player some attack power

    # Place a "Bat" monster adjacent to the player
    bat_health = 10
    bat_attack = 2
    bat = Monster(name="Bat", health=bat_health, attack_power=bat_attack)
    monster_x, monster_y = 2, 1  # North of player (2,2)

    # Ensure the monster tile is valid (e.g. floor)
    monster_tile = engine.world_map.get_tile(monster_x, monster_y)
    if monster_tile:
        monster_tile.type = "floor"
    else:
        # This case should ideally not happen with a simple map
        print(
            f"Error: Monster tile ({monster_x},{monster_y}) is None. Cannot place monster."
        )
        return

    if not engine.world_map.place_monster(bat, monster_x, monster_y):
        print(
            f"Error: Failed to place Bat at ({monster_x},{monster_y}). Tile occupied or invalid?"
        )
        # Check tile explicitly
        tile_at_monster_pos = engine.world_map.get_tile(monster_x, monster_y)
        if tile_at_monster_pos:
            print(
                f"Monster tile details: type={tile_at_monster_pos.type}, monster={tile_at_monster_pos.monster}, item={tile_at_monster_pos.item}"
            )
        return

    # Set input mode (optional for this direct call, but good practice)
    engine.input_mode = "command"

    # Simulate player typing "fight bat" which parser would turn into ("attack", "bat")
    # The game logic converts monster name argument to lower case for comparison.
    # The Monster's actual name is "Bat". The command can be "bat" or "Bat".
    command_tuple = ("attack", "Bat")
    engine.process_command_tuple(command_tuple)

    # Report message_log
    print("message_log content:")
    for message in engine.message_log:
        print(f'- "{message}"')

    # Additional checks (optional, for more detailed verification)
    print("\nAdditional verification:")
    final_bat_tile = engine.world_map.get_tile(monster_x, monster_y)
    if final_bat_tile and final_bat_tile.monster:
        print(f"Bat health after attack: {final_bat_tile.monster.health}")
        if final_bat_tile.monster.health < bat_health:
            print("SUCCESS: Bat health reduced.")
        else:
            print("FAILURE: Bat health NOT reduced.")
    elif not final_bat_tile or not final_bat_tile.monster:  # Bat might be defeated
        if bat_health - engine.player.base_attack_power <= 0:
            print("SUCCESS: Bat defeated and removed from map.")
        else:  # Bat should still be there if not defeated
            print(
                f"FAILURE: Bat unexpectedly removed or tile became None. Initial health: {bat_health}, Player attack: {engine.player.base_attack_power}"
            )

    print(f"Player health after combat: {engine.player.health}")


if __name__ == "__main__":
    main()

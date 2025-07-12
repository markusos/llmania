# Architecture

This project is a classic terminal-based roguelike game implemented in Python.

The main components are:

-   **`src/main.py`**: The entry point of the application. It initializes and runs the game engine.
-   **`src/game_engine.py`**: The central orchestrator of the game. It manages the main game loop, player input, rendering (using the `curses` library), and game state updates. It coordinates interactions between the player, monsters, items, and the game map.
-   **`src/world_generator.py`**: Responsible for creating the game map. It generates the layout of walls and floors, places the player, the goal item (Amulet of Yendor), and distributes other items and monsters.
-   **`src/world_map.py`**: Defines the `WorldMap` class, which represents the game world as a grid of tiles. It provides methods for accessing and modifying tiles, and for managing the placement of items and monsters.
-   **`src/tile.py`**: Defines the `Tile` class, representing a single cell in the world map. Each tile has a type (e.g., wall, floor) and can contain items or monsters.
-   **`src/player.py`**: Defines the `Player` class, including attributes like health, inventory, and attack power, and methods for actions like moving, using items, and attacking.
-   **`src/monster.py`**: Defines the `Monster` class, with attributes for health and attack power, and methods for combat.
-   **`src/item.py`**: Defines the `Item` class, representing objects that the player can find and use. Items have properties that determine their effects.
-   **`src/parser.py`**: Handles parsing of player's text commands into actions that the game engine can understand.

The game operates on a main loop within the `GameEngine`:
1.  The current state of the game (map, player status, messages) is rendered to the terminal.
2.  The engine waits for player input (either direct key presses for movement or text commands).
3.  Input is processed:
    *   Movement keys directly update the player's position.
    *   Text commands are parsed by the `Parser` module.
4.  The game state is updated based on the player's action (e.g., moving the player, initiating combat, using an item).
5.  The loop repeats until a game-ending condition is met (player defeat, victory, or quit).

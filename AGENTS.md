# Agent Development Guide for Text-Based Adventure Game

This document provides guidance for AI agents (like Jules) working on this text-based adventure game codebase.

## Linting and Testing

This project uses `ruff` for code linting and formatting, and `pytest` for running unit tests. Ensure your changes pass linting checks and that all tests pass before submitting.

-   **Ruff (Linting & Formatting)**:
    -   To check for linting errors: `ruff check .`
    -   To automatically format code: `ruff format .`
    -   It's recommended to run these commands from the project root. Configuration for `ruff` can be found in `pyproject.toml`.

-   **Pytest (Unit Testing)**:
    -   To run all unit tests: `pytest`
    -   Tests are located in the `tests/` directory.
    -   Ensure any new code is accompanied by corresponding tests, and that existing tests are updated if necessary.

## Core Architecture

The game is structured around a central `GameEngine` (`src/game_engine.py`) that manages the main game loop, game state, and interactions between various components. Key components include:

-   **`GameEngine`**: Orchestrates the game. It initializes all other major components, runs the game loop, and manages updates to the game state.
-   **`Player` (`src/player.py`)**: Represents the player character, including their position, health, and inventory.
-   **`WorldMap` (`src/world_map.py`)**: Represents the game world, composed of `Tile` objects. It stores the layout of the map, including walls, open spaces, items, and monsters.
-   **`Tile` (`src/tile.py`)**: A single unit of the `WorldMap`. Tiles can be of different types (e.g., wall, floor) and can contain `Item` objects or `Monster` objects.
-   **`CommandProcessor` (`src/command_processor.py`)**: Takes player input (parsed into a verb and optional argument) and dispatches it to the appropriate command object.
-   **`commands/` directory**: Contains all player-executable commands. Each command is a class inheriting from `Command` (`src/commands/base_command.py`).
-   **`Renderer` (`src/renderer.py`)**: Handles displaying the game state to the user. It uses the `curses` library for terminal-based graphics but can also render to a list of strings for debugging.
-   **`InputHandler` (`src/input_handler.py`)**: Captures raw keyboard input from the player.
-   **`Parser` (`src/parser.py`)**: Converts raw player input strings into structured command tuples (e.g., `("move", "north")`).
-   **`MessageLog` (`src/message_log.py`)**: Manages and stores messages to be displayed to the player (e.g., results of actions, descriptions).
-   **`WorldGenerator` (`src/world_generator.py`)**: Responsible for procedurally creating the game map.
-   **`AILogic` (`src/ai_logic.py`)**: Contains logic for an AI to play the game, making decisions about which commands to execute.
-   **`main.py` (`src/main.py`)**: The entry point for the game. It handles command-line arguments (like `--debug` or `--ai`) and starts the `GameEngine`.

## Adding New Commands

To add a new command (e.g., "search"):

1.  **Create a new command class**:
    *   In the `src/commands/` directory, create a new Python file (e.g., `search_command.py`).
    *   Define a class (e.g., `SearchCommand`) that inherits from `Command` (from `src/commands/base_command.py`).
    *   Implement the `__init__` method (calling `super().__init__(...)`) if you need to store the argument or have specific initialization.
    *   Implement the `execute(self) -> Dict[str, Any]` method. This method contains the logic for your command.
        *   It should interact with `self.player`, `self.world_map`, and `self.message_log` as needed.
        *   It **must** return a dictionary, typically `{"game_over": False}`. If the command can end the game, it should return `{"game_over": True}`.
2.  **Register the command**:
    *   Open `src/command_processor.py`.
    *   Import your new command class (e.g., `from src.commands.search_command import SearchCommand`).
    *   In the `CommandProcessor.__init__` method, add your command to the `self._commands` dictionary. The key is the command verb (lowercase string users will type) and the value is the command class itself (e.g., `"search": SearchCommand`).
3.  **Update `src/commands/__init__.py`**:
    *   Export your new command class by adding a line like `from .search_command import SearchCommand`. This makes it easier to import elsewhere.

## Interacting with Key Components

-   **`GameEngine`**:
    *   Generally, commands don't interact directly with the `GameEngine` itself, but rather with components passed to them by the `GameEngine` via the `CommandProcessor` (like `player`, `world_map`, `message_log`).
    *   The `GameEngine` handles the fog of war (`_update_fog_of_war_visibility`) and manages a `visible_map` that is passed to the `Renderer`. Commands operate on the `world_map` (the true state of the world).
-   **`WorldMap`**:
    *   Use `world_map.get_tile(x, y)` to get a `Tile` object at specific coordinates.
    *   Use `world_map.is_blocked(x, y)` to check if a tile is a wall or occupied by a monster.
    *   Tiles have `item` and `monster` attributes, which can be `None` or an instance of `Item` or `Monster`.
-   **`Player`**:
    *   Access player's position via `player.x`, `player.y`.
    *   Modify player's health via `player.health`.
    *   Manage inventory using `player.inventory` (a list of `Item` objects), and methods like `player.add_item()` and `player.remove_item()`.
-   **`MessageLog`**:
    *   Use `message_log.add_message("Your message here")` to display information to the player. These messages are typically shown by the `Renderer`.

## Debug Mode

-   The game can be run in debug mode by passing the `--debug` flag when running `src/main.py` (e.g., `python src/main.py --debug`).
-   In debug mode:
    *   The `curses` interface is not initialized. Game output is printed to the console.
    *   The `GameEngine` is initialized with `debug_mode=True`.
    *   The `Renderer` will output the game state as a list of strings instead of drawing to the screen.
    *   `main_debug()` in `src/main.py` provides an example of how to run specific commands and inspect state in this mode. This is useful for testing game logic without UI complexities.

## Map Algorithms (`src/map_algorithms/`)

This directory contains algorithms for map analysis:
-   **`connectivity.py`**: Checks if all floor tiles on a map are reachable from a starting point.
-   **`density.py`**: Calculates the proportion of wall tiles on the map.
-   **`pathfinding.py`**: Implements A* pathfinding to find routes between points on the map.

These can be used for more advanced world generation, AI decision-making, or game mechanics.

## Rendering and `curses`

-   The `Renderer` (`src/renderer.py`) is responsible for all visual output.
-   When not in `debug_mode`, it uses the `curses` library to create a terminal-based graphical interface.
-   `GameEngine.run()` handles the main loop and calls `renderer.render_all()` to draw the current game state.
-   The `Renderer` takes care of initializing and cleaning up the `curses` environment. If you are making changes to rendering or the main game loop, be mindful of `curses` state management (see `renderer.cleanup_curses()`).

## Testing

-   The `tests/` directory contains unit tests for various components.
-   When adding new features or modifying existing ones, ensure corresponding tests are added or updated.
-   You can run tests using a test runner like `pytest` (which should be configured via `pyproject.toml` and `uv`).

By following these guidelines, you can effectively contribute to the development of this game.

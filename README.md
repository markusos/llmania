# LLMania

A new Python project using uv for package management and Ruff for linting/formatting.

## Setup

1. **Install uv**: If you don't have `uv` installed, follow the official installation instructions at [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/). These instructions cover various platforms and methods.
2. **Create a virtual environment**: Navigate to your project directory and run:
   ```bash
   uv venv
   ```
3. **Activate the environment**:
   - On macOS and Linux: `source .venv/bin/activate`
   - On Windows: `.venv\Scripts\activate`
4. **Install dependencies**: Use `uv sync` to install all dependencies defined in `pyproject.toml`. To include development dependencies like `ruff`, run:
   ```bash
   uv sync --all-extras
   ```
   Or, for only production dependencies:
   ```bash
   uv sync
   ```
   The necessary `curses` library (or `windows-curses` for Windows users) will be automatically installed based on your operating system as defined in `pyproject.toml`.

## Usage

To run the game, execute the following command in your terminal:

```bash
python src/main.py
```

### Gameplay

The game is a terminal-based roguelike adventure.

- **Movement:** Use the arrow keys (Up, Down, Left, Right) or W, A, S, D keys to move your character.
- **Command Mode:**
    - Press `q` to switch to command mode. The input prompt will change to `> `.
    - In command mode, type commands and press Enter.
    - Press `q` or `Escape` while in command mode to return to movement mode.

### Available Commands (in Command Mode)

- `look` or `l`: Describe your current location and any visible items or monsters.
- `take <item name>` or `get <item name>`: Pick up an item from the ground. (e.g., `take Health Potion`)
- `drop <item name>`: Drop an item from your inventory.
- `use <item name>`: Use an item from your inventory. (e.g., `use Health Potion`)
- `inventory` or `i`: Display your current inventory.
- `attack <monster name>`: Attack a monster in your current tile. (e.g., `attack Goblin`)
- `quit` or `q` (while in command mode): Quit the game.

## Overall Architecture

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

## How to Continue Development

This project uses `ruff` for linting and code formatting.

-   **Check for linting issues:** `ruff check .`
-   **Format code:** `ruff format .`

When adding new features or fixing bugs:

-   **Game Logic:** Modifications to game mechanics, new commands, or player/monster interactions will likely involve changes in:
    -   `src/game_engine.py`: For core game loop changes, new action processing.
    -   `src/parser.py`: To add new commands or modify existing command structures.
    -   `src/player.py`, `src/monster.py`, `src/item.py`: For new abilities, attributes, or types of entities.
    -   `src/world_generator.py`: To incorporate new items, monsters, or map features into the world generation process.
-   **New Entities:** New types of items or monsters can be created by adding new classes or by extending existing ones in `src/item.py` and `src/monster.py`. Remember to update `world_generator.py` if you want them to appear in the game.
-   **Map Generation:** Changes to how the world is built are done in `src/world_generator.py`.
-   **Testing:** The project includes a `tests/` directory. It is highly recommended to add new tests for any new functionality or bug fixes. You can run tests using your preferred Python test runner (e.g., `pytest` or the standard `unittest` module). You might need to install `pytest` first: `uv pip install pytest`. Then run `pytest tests/`.

## Future Features and Improvements

This project provides a basic framework for a roguelike game. Here are some ideas for future enhancements:

-   **Advanced Monster AI:**
    -   Pathfinding for monsters to chase the player.
    -   Monsters with ranged attacks or special abilities (e.g., healing, summoning).
    -   Different monster behaviors (e.g., some flee when low on health, some guard specific areas).
-   **Expanded Item System:**
    -   Armor and shields for damage reduction.
    -   Ranged weapons (bows, wands).
    -   Scrolls with various effects (e.g., teleportation, identify item, map reveal).
    -   Potions with diverse effects (e.g., invisibility, temporary stat boosts).
-   **More Monster Variety:**
    -   New monster types with unique stats, abilities, and appearances.
    -   Boss monsters with challenging mechanics.
-   **Game Persistence:**
    -   Saving and loading game progress.
    -   A high score list.
-   **Sophisticated Map Generation:**
    -   Generation of distinct rooms and corridors.
    -   Different dungeon themes or biomes with unique features, items, and monsters.
    -   Traps and hidden doors.
-   **Player Development:**
    -   Player classes (e.g., warrior, mage, rogue) with different starting stats or abilities.
    -   Experience points and leveling up.
    -   A skill tree or attribute improvement system.
-   **Status Effects:**
    -   Positive and negative status effects like poison, confusion, haste, slow, regeneration.
-   **Enhanced Combat Mechanics:**
    -   Critical hits, dodging, blocking.
    -   Turn-based tactical combat with more options than just direct attack.
-   **User Interface Enhancements:**
    -   A more graphical display (perhaps using a library that builds on top of `curses` or a different TUI library).
    -   Better visual feedback for actions and events.
-   **Story and Quests:**
    -   More elaborate quests beyond finding a single item.
    -   NPCs (Non-Player Characters) with dialogue and quests.

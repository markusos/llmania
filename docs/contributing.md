# How to Continue Development

So, you've decided to brave the digital frontier and contribute to LLMania? Excellent! Grab your coding pickaxe and let's get to work.

This project uses `ruff` for linting and code formatting. It's like a digital spellchecker for your code, keeping everything neat and tidy.

-   **Check for linting issues:** `ruff check .`
-   **Format code:** `ruff format .` (Admit it, that's oddly satisfying.)

When adding new features or fixing bugs (especially those pesky AI-generated ones):

-   **Game Logic:** Modifications to game mechanics, new commands, or player/monster interactions will likely involve changes in:
    -   `src/game_engine.py`: For core game loop changes, new action processing. This is the heart of the beast.
    -   `src/parser.py`: To add new commands or modify existing command structures. Teach the game new words!
    -   `src/player.py`, `src/monster.py`, `src/item.py`: For new abilities, attributes, or types of entities. Make things more... interesting.
    -   `src/world_generator.py`: To incorporate new items, monsters, or map features into the world generation process. Spice up the dungeon!
-   **New Entities:** New types of items or monsters can be created by adding new classes or by extending existing ones in `src/item.py` and `src/monster.py`. Remember to update `world_generator.py` if you want them to appear in the game (they don't just magically appear... or do they?).
-   **Map Generation:** Changes to how the world is built are done in `src/world_generator.py`. Fancy yourself a dungeon architect?
-   **Testing:** The project includes a `tests/` directory. It is highly recommended to add new tests for any new functionality or bug fixes. You can run tests using `pytest tests/`. (You might need to install `pytest` first: `uv pip install pytest`). Think of it as quality control for the chaos.
-   **AGENTS.md:** Before you commit your brilliant changes, take a peek at any `AGENTS.md` files. They might contain specific instructions or wisdom from the AI overlords (or just other developers).

Good luck, brave developer. May your code be clean and your bugs be few.

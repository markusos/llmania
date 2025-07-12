# LLMania: Adventures in AI-Generated Chaos

Welcome to LLMania, a glorious, and occasionally terrifying, experiment in AI-powered game development! This isn't just a Python project; it's a journey into the mind of a machine learning model that's been given the keys to the coding kingdom.

Our brave (or perhaps foolish) endeavor involves unleashing [Jules](https://jules.google/), an AI agent from Google, to craft a roguelike game from the digital ether. The mission? To see if an AI can actually build a coherent game. The result? A surprisingly playable, sometimes bizarre, and thoroughly entertaining text-based adventure where you, the player, can wander, loot, and probably get comically defeated by a procedurally generated newt.

## What is this Madness?

Welcome to LLMania, a glorious experiment in AI-powered game development! This project is what happens when you give an AI agent, [Jules](https://jules.google/), a keyboard and a vague idea for a roguelike game. The result? A surprisingly playable, occasionally bizarre, and thoroughly entertaining text-based adventure.

Think of it as a digital archaeological dig. You're exploring the ruins of a game built by a non-human intelligence. Will you find treasure? Bugs? Existential dread? Yes.

So, dive in, explore the code, and for the love of all that is holy, don't take it too seriously. After all, it was written by a machine that's still trying to figure out what a "door" is.

## Summoning the Game: Setup Instructions

Ready to dive into the madness? First, you'll need to get your digital hands dirty with a bit of setup. Don't worry, it's less painful than explaining recursion to a badger.

1.  **Get `uv` (the Cool Kind of UV, Not the Sunburn Kind)**: If `uv` isn't already part of your coding arsenal, head over to the [official `uv` installation guide](https://docs.astral.sh/uv/getting-started/installation/) and grab it. It's like a Swiss Army knife for Python projects, but shinier.
2.  **Craft Your Digital Sandbox (aka Virtual Environment)**: Open your terminal, navigate to the LLMania project directory (you know, where all the magical files live), and type:
    ```bash
    uv venv
    ```
    This creates a cozy little isolated space for our game, so it doesn't throw a tantrum and mess with your other Python projects.
3.  **Activate the Portal (Your Virtual Environment, That Is)**:
    *   On macOS and Linux, chant: `source .venv/bin/activate`
    *   On Windows, incant: `.venv\Scripts\activate`
    If your prompt changes, congratulations! You've successfully entered the Matrix... or, well, activated the environment.
4.  **Install the Arcane Tomes (Dependencies, We Mean Dependencies)**: With your environment active, it's time to install all the necessary bits and bobs. `uv` makes this a breeze:
    *   For the full experience, including developer tools (like `ruff`, our trusty code linter/formatter):
        ```bash
        uv sync --dev
        ```
    *   If you're just here to play and don't care about the messy behind-the-scenes stuff (production dependencies only):
        ```bash
        uv sync
        ```
    Our mystical `pyproject.toml` file will guide `uv` to fetch everything needed, including the `curses` library (or `windows-curses` for our Windows-using friends) that paints the game on your terminal.

## Let the LLMania Begin! (How to Run & Play)

Alright, setup complete? Virtual environment humming? Excellent. It's time to unleash the beast!

To start your grand adventure (or misadventure, results may vary), fire up your terminal and run:

```bash
uv run python src/main.py
```

And just like that, you're in! Welcome to a world rendered entirely in the glorious, retro-chic medium of text.

### Navigating Your Textual Doom (Gameplay Basics)

This is a terminal-based roguelike, which means your imagination is half the graphics card.

*   **Stretching Your Legs (Movement):**
    *   Use the **arrow keys** (Up, Down, Left, Right) to explore.
    *   Alternatively, if you're a cool WASD kid, those work too!
*   **Talking to the Game (Command Mode):** Sometimes, pointing and grunting (with arrow keys) isn't enough. You need to *tell* the game what you want.
    *   Press the **Tilde (`~`) key** to enter Command Mode. Your prompt will change to a sophisticated `> `, eagerly awaiting your instructions.
    *   Type your desired command (see the list below for your options) and hit **Enter**.
    *   Want to go back to just moving around? Press **Tilde (`~`)** again, or the **Escape** key. Freedom!

### Developer's Corner: Special Launch Options

Feeling adventurous? Try these command-line arguments for a different kind of fun:

*   **Debug Mode (`--debug`)**: Want to see the Matrix? Run the game with the `--debug` flag to get a simplified, non-interactive view of the game state. It's perfect for testing and seeing what the AI is *really* thinking.
    ```bash
    uv run python src/main.py --debug
    ```
*   **AI Mode (`--ai`)**: Feeling lazy? Let the AI play the game for you! Use the `--ai` flag to watch the AI try to win its own game. It's like a screensaver, but with more existential dread.
    ```bash
    uv run python src/main.py --ai
    ```
    You can even control the AI's "thinking" speed with the `--ai_sleep` argument (e.g., `--ai_sleep 0.2` for a speed demon AI).

### Your Lexicon of Power (Available Commands)

Once in Command Mode (`~`), here's how you can interact with the world (or at least, try to):

*   `look` (or `l` for the laconic): "Computer, enhance!" This describes your current surroundings, including any shiny loot or grumpy monsters.
*   `take <item name>` (or `get <item name>`): See something you like? "Yoink!" it off the floor. Example: `take Health Potion` (because you *will* need it).
*   `drop <item name>`: Feeling encumbered? Unburden yourself. Example: `drop Slightly Chewed Rock`.
*   `use <item name>`: Time to unleash the power of that... thing you picked up. Example: `use Health Potion` (hopefully before it's too late).
*   `inventory` (or `i`): "What's in my pocketses?" Displays your hard-earned (or questionably acquired) treasures.
*   `attack <monster name>`: Engage in glorious combat! Or, more accurately, tell the game you want to whack that `Goblin` (or whatever else is looking at you funny). Example: `attack Grumpy Goblin`.
*   `quit` (or `q`): "I've seen enough!" Makes a graceful (or rage-filled) exit from the game. Only works in command mode, naturally.

## Peeking Under the Hood: The Architecture

Curious about how this digital Frankenstein was assembled? For a detailed look at the game's components and how they interact (or occasionally collide), check out the [Architecture Document](./docs/architecture.md).

## Wielding the Code Hammer: Contributing to LLMania

Feeling brave enough to dive into the code? Whether you want to fix a bug, add a feature, or just poke around, our [Contributing Guide](./docs/contributing.md) has tips on how to get started, run tests, and generally not break everything (too much).

## The Crystal Ball: Future Features & Wild Ideas

What does the future hold for LLMania? More chaos? More features? Sentient teapots? Explore the possibilities in our [Future Features Document](./docs/future_features.md).

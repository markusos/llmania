"""
Main entry point for the text-based adventure game.

This script handles:
- Setting up the Python path to correctly import game modules.
- Initializing and running the game engine.
- Providing a debug mode for testing game mechanics without the curses interface.
- Basic error handling for the game loop.
"""

import argparse
import os
import sys
import traceback

# --- Path setup ---
# Ensure the project root is in sys.path for module resolution.
# This allows `from src.game_engine import GameEngine` etc. to work correctly
# when running main.py directly from the project's root or any other location.
# It assumes main.py is in the 'src' directory or a similar structure.
try:
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    # __file__ might not be defined if running in certain environments (e.g. some REPLs)
    # Fallback or log an error if necessary. For typical script execution, this is fine.
    print("Warning: Could not set up sys.path. Ensure project root is in PYTHONPATH.")


from game_engine import GameEngine  # noqa: E402 (ignore import not at top of file)

# --- End Path setup ---

# Note: The 'curses' import is generally handled within the Renderer or GameEngine.
# If direct curses interaction is needed in main.py (e.g., for fallback error handling),
# it can be imported here, but typically it's encapsulated.


def main_debug():
    """
    Runs the game in a debug mode without the curses interface.
    This allows for printing game state and messages directly to the console,
    which is useful for testing game logic and content generation.
    """
    print("--- Starting Game in Debug Mode ---")
    # Initialize game engine in debug mode.
    # Smaller map for easier console output.
    game = GameEngine(map_width=20, map_height=10, debug_mode=True)

    # --- Initial State Output ---
    print("\n--- Initial Player and Map State ---")
    print(f"Player initial position: ({game.player.x}, {game.player.y})")
    print(f"Player initial health: {game.player.health}")
    print(f"Winning position: {game.winning_position}")

    # Initial render to list (debug_render_to_list=True is handled by GameEngine)
    map_representation = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,  # Explicitly true for clarity in main_debug
    )
    if map_representation:
        print("\n--- Initial Map Display (as list of strings) ---")
        for row in map_representation:
            print(row)
    else:
        print("Error: Failed to render map for debugging.")

    # --- Simulate and Test Basic Interactions ---
    # Note: In debug mode, GameEngine.run() might not loop.
    # We directly call CommandProcessor methods to simulate turns.

    print("\n--- Simulating 'look' command ---")
    game.message_log.clear()  # Clear previous messages
    game.command_processor.process_command(
        parsed_command_tuple=("look", None),
        player=game.player,
        world_map=game.world_map,
        message_log=game.message_log,
        winning_position=game.winning_position,
    )
    # Render and display output after 'look'
    output_after_look = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,
    )
    if output_after_look:
        print("--- Output after 'look' ---")
        for row in output_after_look:  # Display full output for context
            print(row)
    else:
        print("Error: Failed to render after 'look'.")

    print("\n--- Simulating 'move east' command ---")
    game.message_log.clear()
    game.command_processor.process_command(
        parsed_command_tuple=("move", "east"),
        player=game.player,
        world_map=game.world_map,
        message_log=game.message_log,
        winning_position=game.winning_position,
    )
    output_after_move = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,
    )
    if output_after_move:
        print("--- Output after 'move east' ---")
        for row in output_after_move:
            print(row)
    else:
        print("Error: Failed to render after 'move east'.")

    print("\n--- Simulating 'take' command (expecting 'nothing to take') ---")
    game.message_log.clear()
    # Assuming player moved to an empty spot.
    game.command_processor.process_command(
        parsed_command_tuple=("take", None),  # Or specify a non-existent item
        player=game.player,
        world_map=game.world_map,
        message_log=game.message_log,
        winning_position=game.winning_position,
    )
    output_after_take = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,
    )
    if output_after_take:
        print("--- Output after 'take' attempt ---")
        for row in output_after_take:
            print(row)
    else:
        print("Error: Failed to render after 'take' attempt.")

    print("\n--- Debug Mode Finished ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the text-based adventure game.")
    parser.add_argument(
        "--debug", action="store_true", help="Run the game in debug mode."
    )
    parser.add_argument(
        "--ai", action="store_true", help="Activate AI mode for automated gameplay."
    )
    parser.add_argument(
        "--ai_sleep",
        type=float,
        default=0.5,
        help="Delay in seconds between AI actions.",
    )
    args = parser.parse_args()

    if args.debug:
        main_debug()
    else:
        # Initialize and run the game with the curses interface.
        # Larger map for the actual game.
        game = GameEngine(
            map_width=30,
            map_height=15,
            debug_mode=False,
            ai_active=args.ai,
            ai_sleep_duration=args.ai_sleep,
        )
        try:
            game.run()
        except Exception as e:
            # This is a top-level catch-all for unexpected errors during game.run().
            # GameEngine.run() has its own finally block for curses cleanup,
            # but this catches errors that might occur before or outside that,
            # or if the cleanup itself fails.
            print("-" * 70)
            print("The game encountered an unhandled error:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {e}")
            print("Traceback:")
            print(traceback.format_exc())
            print("-" * 70)
            print("Attempting to restore terminal state...")
            # Attempt to restore terminal state if curses was involved.
            # This is a fallback; GameEngine should handle its own cleanup.
            try:
                import curses  # Import here to avoid dependency if not used.

                if curses.has_colors():  # Check if curses was initialized
                    curses.echo()
                    curses.nocbreak()
                    curses.endwin()
                print("Terminal state restoration attempt complete.")
            except Exception as cleanup_error:
                print(f"Error during fallback terminal cleanup: {cleanup_error}")
                print("Terminal might be in an inconsistent state.")

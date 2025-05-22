import sys
import os

if __name__ == "__main__":
    # Get the absolute path of the directory containing main.py (src)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the absolute path of the project root (parent of src)
    project_root = os.path.dirname(src_dir)
    # Add project_root to the beginning of sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from src.game_engine import GameEngine

if __name__ == "__main__":
    # You can adjust map_width and map_height here if desired
    game = GameEngine(map_width=30, map_height=15)
    game.run()

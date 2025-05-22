from .game_engine import GameEngine

if __name__ == "__main__":
    # You can adjust map_width and map_height here if desired
    game = GameEngine(map_width=30, map_height=15)
    game.run()

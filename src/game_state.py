from __future__ import annotations

from enum import Enum, auto


class GameState(Enum):
    PLAYING = auto()
    GAME_OVER = auto()
    INVENTORY = auto()
    QUIT = auto()

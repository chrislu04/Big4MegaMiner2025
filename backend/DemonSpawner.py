import Constants
from GameState import GameState

class DemonSpawner:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.reload_time_left = Constants.DEMON_SPAWNER_RELOAD_TURNS
    
    def __update__(self, game_state: GameState) -> None:
        pass # TODO
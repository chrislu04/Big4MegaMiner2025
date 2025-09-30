import Constants
from GameState import GameState

class DemonSpawner:
    def __init__(self, x: int, y: int, target_team: str) -> None:
        self.x = x
        self.y = y
        self.reload_time_left = Constants.DEMON_SPAWNER_RELOAD_TURNS
        self.target_team = target_team
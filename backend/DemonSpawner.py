import Constants
from GameState import GameState

class DemonSpawner:
    def __init__(self, x: int, y: int, target_team: str, spawn_directionX : int, spawn_directionY : int) -> None:
        self.x = x
        self.y = y
        self.reload_time_max = Constants.DEMON_SPAWNER_RELOAD_TURNS
        self.reload_time_left = self.reload_time_max
        self.target_team = target_team
        self.spawn_directionX = spawn_directionX
        self.spawn_directionY = spawn_directionY
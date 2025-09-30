import Constants
from Entity import Entity

class Demon:
    def __init__(self, x: int, y: int, target_team: str) -> None:
        self.hp = Constants.DEMON_INITIAL_HP
        self.x = x
        self.y = y
        self.target_team = target_team
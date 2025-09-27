import Constants
from Entity import Entity

class Demon:
    def __init__(self, x: int, y: int) -> None:
        self.hp = Constants.DEMON_INITIAL_HP
        self.x = x
        self.y = y
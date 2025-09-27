import Constants
import math

class Demon:
    def __init__(self, x: int, y: int) -> None:
        self.hp = Constants.DEMON_INITIAL_HP
        self.x = x
        self.y = y
        self.attack_power = Constants.DEMON_ATTACK_POWER
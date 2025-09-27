import Constants
import math

class Mercenary:
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = Constants.MERCENARY_INITIAL_HP
        self.x = x
        self.y = y
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?
        self.attack_power = Constants.MERCENARY_ATTACK_POWER
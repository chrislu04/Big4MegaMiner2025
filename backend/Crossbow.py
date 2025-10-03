import Constants
from Tower import Tower

class Crossbow(Tower):
    def __init__(self, x: int, y: int, team_color: str):
        super().__init__(x, y, team_color, Constants.CROSSBOW_MAX_COOLDOWN, Constants.CROSSBOW_RANGE, Constants.CROSSBOW_DAMAGE, Constants.CROSSBOW_PRICE)
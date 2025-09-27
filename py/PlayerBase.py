import Constants
import math

class PlayerBase:
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = Constants.PLAYER_BASE_INITIAL_HP
        self.x = x
        self.y = y
        self.mercenaries_queued = 0
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Player base team_color must be 'r' or 'b'") # TF2 reference?
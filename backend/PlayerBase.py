import Constants

class PlayerBase():
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = Constants.PLAYER_BASE_INITIAL_HP
        self.x = x
        self.y = y
        self.mercenary_queued_up : int = 0
        self.mercenary_queued_down : int = 0
        self.mercenary_queued_left : int = 0
        self.mercenary_queued_right : int = 0

        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Player base team_color must be 'r' or 'b'") # TF2 reference?
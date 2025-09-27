import Constants

class PlayerBase(Entity):
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = Constants.PLAYER_BASE_INITIAL_HP
        self.x = x
        self.y = y
        self.mercenary_queued_up
        self.mercenary_queued_down
        self.mercenary_queued_left
        self.mercenary_queued_right

        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Player base team_color must be 'r' or 'b'") # TF2 reference?
    
    def __update__(self, game_state: GameState):
        pass # doesn't do anything actively
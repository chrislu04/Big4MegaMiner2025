import Constants
import math

class GameState:
    def __init__(self, team_color: str) -> None:
        self.turns_progressed = 0
        self.victory = None
        if team_color in ['r','b']:
            self.team_color = team_color
        else:
            raise Exception("Player team_color must be 'r' or 'b'")
        self.team_name = None
        self.money = Constants.INITIAL_MONEY

        # Map specifications
        self.map_width = None
        self.map_height = None
        self.entity_grid = [] # This is going to be a 2D array, needs input from map_width and map_height

        self.player_base_r = None # call PlayerBase() to define more, PlayerBase.py still needs updated
        self.player_base_b = None # call PlayerBase() to define more, PlayerBase.py still needs updated

        # Arrays that will hold the active entities for each type
        self.mercs = []
        self.towers = []
        self.demons = []
        self.demon_spawners = []
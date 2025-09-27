import Constants
import math

class GameState:
    def __init__(self, team_color: str, map_width: int, map_height: int) -> None:
        self.turns_progressed = 0
        self.victory = None
        if team_color in ['r','b']:
            self.team_color = team_color
        else:
            raise Exception("Player team_color must be 'r' or 'b'")
        self.team_name = None
        self.money = Constants.INITIAL_MONEY

        # Map specifications
        self.map_width = map_width
        self.map_height = map_height
        # This grid is just "0" for now, but the width and height are set
        self.entity_grid = [ [0 for i in range(map_height)] , [0 for i in range(map_width)]]
        self.tile_grid = [] # List of strings

        self.player_base_r = None # call PlayerBase() to define more, PlayerBase.py still needs updated
        self.player_base_b = None # call PlayerBase() to define more, PlayerBase.py still needs updated

        # Arrays that will hold the active entities for each type
        self.mercs = []
        self.towers = []
        self.demons = []
        self.demon_spawners = []
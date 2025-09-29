import Constants
import math

class GameState:
    def __init__(self, team_color: str, map_width: int, map_height: int) -> None:
        self.turns_progressed = 0
        self.victory = None
        self.team_name_r = None
        self.team_name_b = None
        self.money_r = Constants.INITIAL_MONEY
        self.money_b = Constants.INITIAL_MONEY

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
        # Do we need the split these into per-team lists? Like having towers_r and towers_b?
        self.towers = []
        self.demons = []
        self.demon_spawners = []
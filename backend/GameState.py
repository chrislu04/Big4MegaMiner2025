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

        # TODO: this should come from parameters to this contructor function
        self.entity_grid = [ [0 for i in range(map_height)] , [0 for i in range(map_width)]]
        self.tile_grid = [] # List of strings

        # TODO: this should come from parameters to this constructor function
        self.player_base_r = None # call PlayerBase() to define more, PlayerBase.py still needs updated
        self.player_base_b = None # call PlayerBase() to define more, PlayerBase.py still needs updated

        # Arrays that will hold the active entities for each type
        self.mercs = []
        self.towers = []
        self.demons = []
        self.demon_spawners = []

        # Compute mercenary paths, from Red to Blue player bases
        self.mercenary_path_left  = [] # start from left-adjacent tile to player base
        self.mercenary_path_right = [] # start from left-adjacent tile to player base
        self.mercenary_path_up    = [] # start from left-adjacent tile to player base
        self.mercenary_path_down  = [] # start from left-adjacent tile to player base

        if self.tile_grid[][]

import Constants
import math
import PlayerBase

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
        self.player_base_r : PlayerBase = PlayerBase() # call PlayerBase() to define more, PlayerBase.py still needs updated
        self.player_base_b : PlayerBase = PlayerBase() # call PlayerBase() to define more, PlayerBase.py still needs updated

        # Arrays that will hold the active entities for each type
        self.mercs = []
        self.towers = []
        self.demons = []
        self.demon_spawners = []

        # Compute mercenary paths, from Red to Blue player bases
        self.mercenary_path_left  = self.compute_mercenary_path((player_base_r.x-1, player_base_r.y))
        self.mercenary_path_right = self.compute_mercenary_path((player_base_r.x+1, player_base_r.y))
        self.mercenary_path_up    = self.compute_mercenary_path((player_base_r.x, player_base_r.y-1))
        self.mercenary_path_down  = self.compute_mercenary_path((player_base_r.x, player_base_r.y+1))

    def compute_mercenary_path(self, start_point: tuple) -> list:
        # See if there's a path starting at the starting point
        if self.tile_grid[start_point.x][start_point.y] == 'Path':
            # Do bastard DFS algorithm: raise exception if there's any branch in the path
            computed_path = [start_point]
            current_tile = start_point
            traversed = set()
            traversed.add(start_point)

            # Loop through new neighboring tiles until there are none left or a branch is detected
            while current_tile != None:
                # Find the next tile in the path
                for neighbor in [
                    (current_tile.x - 1, current_tile.y)
                    (current_tile.x + 1, current_tile.y)
                    (current_tile.x, current_tile.y - 1)
                    (current_tile.x, current_tile.y + 1)
                ]:
                    current_tile = None
                    if neighbor not in traversed and self.tile_grid[neighbor.x][neighbor.y] == 'Path':
                        traversed.add(neighbor)
                        if current_tile == None: current_tile = neighbor
                        else: raise Exception('Branching detected in mercenary path')
                
                # Record the next tile
                computed_path.append(current_tile) 
        else:
            return None

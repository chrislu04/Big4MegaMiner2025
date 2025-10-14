import Constants
import math
from PlayerBase import PlayerBase
# from PIL import Image
# import numpy as np

class GameState:
    ## Does game state need team_color?
    def __init__(self, team_color: str, map_width: int, map_height: int) -> None:
        self.turns_progressed = 950
        self.victory = None
        self.team_name_r = None
        self.team_name_b = None
        self.money_r = Constants.INITIAL_MONEY
        self.money_b = Constants.INITIAL_MONEY

        # Map specifications
        self.map_width = map_width
        self.map_height = map_height
        
        self.tile_grid = [ ## Default Map
            ['r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'], 
            ['r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'], 
            ['r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'], 
            ['r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'r'], 
            ['r', 'r', 'Path', 'Path', 'r', 'base', 'r', 'Path', 'Path', 'r', 'r'], 
            ['r', 'r', 'Path', 'r', 'r', 'r', 'r', 'r', 'Path', 'r', 'r'], 
            ['r', 'r', 'Path', 'r', 'r', 'Path', 'r', 'r', 'Path', 'r', 'r'], 
            ['r', 'r', 'Path', 'r', 'r', 'Path', 'r', 'r', 'Path', 'r', 'r'], 
            ['_', '_', 'Path', '_', '_', 'Path', '_', '_', 'Path', '_', '_'], 
            ['_', '_', 'Path', '_', '_', 'Path', '_', '_', 'Path', '_', '_'], 
            ['_', '_', 'Path', '_', '_', 'Path', '_', '_', 'Path', '_', '_'], 
            ['_', '_', 'Path', '_', '_', 'Path', '_', '_', 'Path', '_', '_'], 
            ['_', '_', 'Path', '_', '_', 'Path', '_', '_', 'Path', '_', '_'], 
            ['b', 'b', 'Path', 'b', 'b', 'Path', 'b', 'b', 'Path', 'b', 'b'], 
            ['b', 'b', 'Path', 'b', 'b', 'Path', 'b', 'b', 'Path', 'b', 'b'], 
            ['b', 'b', 'Path', 'b', 'b', 'b', 'b', 'b', 'Path', 'b', 'b'], 
            ['b', 'b', 'Path', 'Path', 'b', 'base', 'b', 'Path', 'Path', 'b', 'b'], 
            ['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'], 
            ['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'], 
            ['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'], 
            ['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'], 
            ['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b']
            ]
        
        # TODO: this should come from parameters to this contructor function
        # self.entity_grid = [ [0 for i in range(map_height)] , [0 for i in range(map_width)]] # <-- This doens't work as intended

        self.entity_grid = []
        for i in range(len(self.tile_grid)):
            row = [None] * len(self.tile_grid[0])
            self.entity_grid.append(row)
        
        # TODO: this should come from parameters to this constructor function
        self.player_base_r : PlayerBase = PlayerBase(4,5,"r") # call PlayerBase() to define more, PlayerBase.py still needs updated
        self.player_base_b : PlayerBase = PlayerBase(16,5,"b") # call PlayerBase() to define more, PlayerBase.py still needs updated
        self.entity_grid[4][5] = "base"
        self.entity_grid[16][5] = "base"
        # self.entity_grid[9][5] = "spawner"
        # self.entity_grid[11][5] = "spawner"
        # Arrays that will hold the active entities for each type
        self.mercs = []
        self.towers = []
        self.demons = []
        self.demon_spawners = []

        # Compute mercenary paths, from Red to Blue player bases
        self.mercenary_path_left  = self.compute_mercenary_path((self.player_base_r.x-2, self.player_base_r.y))
        self.mercenary_path_right = self.compute_mercenary_path((self.player_base_r.x+2, self.player_base_r.y))
        self.mercenary_path_up    = self.compute_mercenary_path((self.player_base_r.x, self.player_base_r.y-2))
        self.mercenary_path_down  = self.compute_mercenary_path((self.player_base_r.x, self.player_base_r.y+2))


    ##Uses RGB values to construct a map, full red is red terratoy, full blue is blue terrarort, full green is path, black is void
    ##using r, b, and # == path, _ = void
    # def make_tile_grid_from_image(self):
    #     map_image_path = "C:/Users/kenji/OneDrive/Desktop/GitHub Projects/MegaMiner2025/backend/maps/map.png"
    #     image = Image.open(map_image_path)
    #     pix_arry = np.asarray(image)
    #     tile_grid = []
    #     for x in range(len(pix_arry[0])):
    #         row = []
    #         for y in range(len(pix_arry)):
    #             if pix_arry[y][x][0] == 255 and pix_arry[y][x][1] == 0 and pix_arry[y][x][2] == 0:
    #                 row.append('r')
    #             elif pix_arry[y][x][0] == 0 and pix_arry[y][x][1] == 255 and pix_arry[y][x][2] == 0:
    #                 row.append('Path')
    #             elif pix_arry[y][x][0] == 0 and pix_arry[y][x][1] == 0 and pix_arry[y][x][2] == 255:
    #                 row.append('b') ## I see that we're using path in compute_merc(), so Ill make it path on the grid
    #             elif pix_arry[y][x][0] == 0 and pix_arry[y][x][1] == 0 and pix_arry[y][x][2] == 0:
    #                 row.append('_')
    #             elif pix_arry[y][x][0] == 255 and pix_arry[y][x][1] == 255 and pix_arry[y][x][2] == 0:
    #                 row.append('base')
    #         tile_grid.append(row)

    #     return tile_grid
    
    def compute_mercenary_path(self, start_point: tuple) -> list:
        if self.tile_grid[start_point[0]][start_point[1]] == 'Path':
            # Do bastard DFS algorithm: raise exception if there's any branch in the path
            computed_path = [start_point]
            current_tile = start_point
            traversed = set()
            traversed.add(start_point)

            # Loop through new neighboring tiles until there are none left or a branch is detected
            while current_tile != None:
                # print("Current Tile", current_tile)
                # Find the next tile in the path
                for neighbor in [
                    (current_tile[0] - 1, current_tile[1]),
                    (current_tile[0] + 1, current_tile[1]),
                    (current_tile[0], current_tile[1] - 1),
                    (current_tile[0], current_tile[1] + 1)
                ]:
                    current_tile = None
                    # print("Neighbor", neighbor)
                    if neighbor not in traversed and self.tile_grid[neighbor[0]][neighbor[1]] == 'Path':
                        traversed.add(neighbor)
                        if current_tile == None: current_tile = neighbor
                        else: raise Exception('Branching detected in mercenary path')
                        break # <- The for loop always sets current tile to none, thus always ending the while loop. So we break once we find the neighbor
                
                # Record the next tile
                # print("Neighbor Chosen ", current_tile)
                if current_tile != None: ## The last path will always be None, so we write this to exlude it
                    computed_path.append(current_tile)

            return computed_path ## Forgot this line
        else:
            return None

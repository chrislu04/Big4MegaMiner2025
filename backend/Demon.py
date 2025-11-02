import Constants
from Entity import Entity
from GameState import GameState
from PlayerBase import PlayerBase
import Utils

class Demon:
    def __init__(self, x: int, y: int, target_team: str, game_state: GameState) -> None:
        self.health = Constants.DEMON_INITIAL_health
        self.x = x
        self.y = y
        self.target_team = target_team
        self.state = 'moving'

        self.current_path = []
        possible_paths = [
            game_state.mercenary_path_down, 
            game_state.mercenary_path_left,
            game_state.mercenary_path_right,
            game_state.mercenary_path_up
        ]
        # Assumes no overlapping paths. If merc is on any path tile in path, we are on that path
        for path in possible_paths:
            if path == None: #<- in case there aren't 4 paths, it will skip iterating over a none value (which cases an error)
                continue 
            if (self.x, self.y) in path:
                self.current_path = path
                
    # Helper function do find what path this merc is on. 
    def get_current_path(self):
        # return current path and position along current path
        return (self.current_path, self.current_path.index((self.x, self.y)))
    
    # Helper function that returns coordinates of the path tile forward or back from the merc's pos
    def get_adjacent_path_tile(self, game_state: GameState, delta: int):
        path_data = self.get_current_path()
        path = path_data[0]
        path_pos = path_data[1]

        # if we are at the end of path, return last tile 
        # otherwise, return next tiles
        delta *= 1 if self.target_team == 'r' else -1
        return path[Utils.clamp(path_pos + delta, 0, len(path)-1)]
    
    def set_behind_waiting(self, game_state: GameState):
        behind_pos = self.get_adjacent_path_tile(game_state, -1)
        behind_entity = game_state.entity_grid[behind_pos[1]][behind_pos[0]]
        # base case: we are in the first tile in our path, do not recurse
        if self.x == behind_pos[0] and self.y == behind_pos[1]:
            return
        # base case: entity in behind pos does not contain merc
        elif type(behind_entity) != Demon:
            return
        else:
            behind_entity.state = 'waiting'
            behind_entity.set_behind_waiting(game_state)

    # If in range to attack a player base, return a reference to that player base,
    # Otherwise, return None
    def get_attackable_player_base(self, game_state: GameState) -> PlayerBase:
        if self.current_path.index((self.x,self.y)) == len(self.current_path) - 2:
            return game_state.player_base_b
        elif self.current_path.index((self.x,self.y)) == 1:
            return game_state.player_base_r
        else:
            return None
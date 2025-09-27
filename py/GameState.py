import Constants
import math

# Probably going to merge these two classes into one main function
# Also, define the map with a 2D Array

class PlayerState:
    def __init__(self, team_color: str) -> None:
        if team_color in ['r','b']:
            self.team_color = team_color
        else:
            raise Exception("Player team_color must be 'r' or 'b'")
        team_name = None
        money = Constants.INITIAL_MONEY
        self.mercenaries = list()
        self.towers = list()

class GameState:
    def __init__(self) -> None:
        self.turns_progressed = 0
        self.victory = None
        self.map_width = None
        self.map_height = None
        self.player_state_r = PlayerState('r')
        self.player_state_b = PlayerState('b')
        self.map_tiles = dict() # (x,y) -> blue territory, red territory, path, etc.
        self.entity_lookup = dict() # (x,y) -> Mercenary, Enemy, Tower, Spawner, etc.
        self.enemies = list()
        self.enemy_spawners = list()
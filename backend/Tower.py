from Entity import Entity
from Mercenary import Mercenary
import math
from PlayerBase import PlayerBase

class Tower(Entity):
    def __init__(self, x: int, y: int, team_color: str, cooldown: int, range : int, attack : int , value : int, playerbase : PlayerBase = None):
        super().__init__(1, value, attack, x, y)
        self.cooldown_max = cooldown
        self.current_cooldown = 0
        self.tower_range = range
        self.path = []
        self.angle = 90

        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Tower team_color must be 'r' or 'b'") # TF2 reference?
    
    ## Called when a tower gets added to the grid
    def buildt(self, map_array):
        self.path = self.find_all_paths_in_range(map_array)
        # print(self.path)
    
    ## Called everytime the world updates
    def update(self, entity_array):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            self.tower_activation(entity_array)
    
    ## Called whenever the cooldown is up
    def tower_activation(self, entity_array):
        for path in self.path:
            whats_on_path = entity_array[path[0]][path[1]] ## I don't want to type out the entity array thing more than once lol

            if isinstance(whats_on_path, Mercenary): ## if the ent
                if whats_on_path.team != self.team:
                    whats_on_path.health -= self.attack_power
                    # print(whats_on_path.health)
                    self.current_cooldown = self.cooldown_max
                    self.angle = math.atan2(path[1] - self.y, path[0] - self.x)


    def find_all_paths_in_range(self, map_array) -> list:
        paths = []
        for xi in range(self.x - self.tower_range, self.x + self.tower_range):
            for yi in range(self.y - self.tower_range, self.y + self.tower_range):
                if xi == self.x and yi == self.y: continue
                
                if math.sqrt((xi - self.x) * (xi - self.x) + (yi - self.y) * (yi - self.y)) <= self.tower_range: ##This is the circle equation, I like my tower range to be circles 
                    if map_array[xi][yi] == 'Path': ## We're using the tile grid since we don't need to know the entities to know where a path is
                        paths.append((xi,yi))

        ## It is currently sorted by top-left to bottom-right, change it later based on closet first, weakest second
        return paths

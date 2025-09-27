import Constants
import math

class Tower:
    def __init__(self, x: int, y: int, tower_type: TowerType, team_color: str) -> None:
        self.x = x
        self.y = y
        self.tower_type = tower_type
        # BALANCE: initial reload formula: encourange long-term planning, but not too much
        # BALANCE: don't let the initial reload time be zero
        #self.reload_turns_left = math.ceil(self.tower_type.reload_turns//2)
        self.kills = 0
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?

    def __update__(self, tower_type: TowerType) -> None:
        # still working on this part, doesn't really work yet

        #self.tower_type = tower_type
        
        #if tower_type == 'house':
        #    print("HOUSE GENERATED MONEY")
        pass
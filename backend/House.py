import Constants
from Tower import Tower

class House(Tower):
    def __init__(self, x: int, y: int, team_color: str) -> None:
        super().__init__(self, x, y, team_color, Constants.MINIGUN_MAX_COOLDOWN, Constants.MINIGUN_RANGE, Constants.MINIGUN_DAMAGE, Constants.MINIGUN_PRICE)

        self.money_gain = Constants.HOUSE_MONEY_PRODUCED
    
    def update(self, game_state):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            self.tower_activation(game_state)
    
    def tower_activation(self, game_state):
        if self.team == "r":
            game_state.money_r += self.money_gain
        elif self.team == "b":
            game_state.money_b += self.money_gain
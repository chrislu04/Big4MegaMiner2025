import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name
from Utils import log_msg, get_increased_tower_price

class House(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState):
        super().__init__(
            x, y,
            team_color,
            Constants.HOUSE_MAX_COOLDOWN,
            Constants.HOUSE_RANGE,
            Constants.MINIGUN_DAMAGE, # "I would be dangerous, I just don't FEEL like it!"
            game_state.house_price,
            game_state
        )

        game_state.house_price = get_increased_tower_price(game_state.house_price, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)

        self.angle = 0
        self.name = select_tower_name('H', self.team)
    
    def update(self, game_state):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            self.tower_activation(game_state)
    
    def tower_activation(self, game_state : GameState):
        if self.team == "r":
            game_state.money_r += Constants.HOUSE_MONEY_PRODUCED
            log_msg(f'House {self.name} produced ${Constants.HOUSE_MONEY_PRODUCED} for the Red team. Total = ${game_state.money_r}')
        elif self.team == "b":
            game_state.money_b += Constants.HOUSE_MONEY_PRODUCED
            log_msg(f'House {self.name} produced ${Constants.HOUSE_MONEY_PRODUCED} for the Blue team. Total = ${game_state.money_b}')
        self.current_cooldown = Constants.HOUSE_MAX_COOLDOWN
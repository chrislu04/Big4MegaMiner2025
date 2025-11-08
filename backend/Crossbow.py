import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name
from Utils import get_increased_tower_price

class Crossbow(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState):
        super().__init__(
            x, y,
            team_color,
            Constants.CROSSBOW_MAX_COOLDOWN,
            Constants.CROSSBOW_RANGE,
            Constants.CROSSBOW_DAMAGE,
            game_state.minigun_price,
            game_state
        )

        game_state.crossbow_price = get_increased_tower_price(game_state.crossbow_price, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)

        self.name = select_tower_name('CR', self.team)
    
    def tower_activation(self, game_state: GameState):
        super().shoot_single_priority_target(game_state)
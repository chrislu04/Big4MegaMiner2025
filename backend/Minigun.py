import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name

class Minigun(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState) -> None:
        super().__init__(
            x, y,
            team_color,
            Constants.MINIGUN_MAX_COOLDOWN,
            Constants.MINIGUN_RANGE,
            Constants.MINIGUN_DAMAGE,
            Constants.MINIGUN_PRICE,
            game_state
        )
        
        Constants.MINIGUN_PRICE += Constants.TOWER_PRICE_INCREASE_PER_BUY

        self.name = select_tower_name('M',self.team)
    
    def tower_activation(self, game_state: GameState):
        super().shoot_all_targets_in_range(game_state)
import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name

class Cannon(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState) -> None:
        super().__init__(
            x, y,
            team_color,
            Constants.CANNON_MAX_COOLDOWN,
            Constants.CANNON_RANGE,
            Constants.CANNON_DAMAGE,
            Constants.CANNON_PRICE,
            game_state
        )

        Constants.CANNON_PRICE += Constants.TOWER_PRICE_INCREASE_PER_BUY;

        self.radius = 2 # Cannon shots have a splash radius, this variable shows that
        
        self.name = select_tower_name('CA', self.team)
    
    def tower_activation(self, game_state: GameState):
        super().shoot_single_priority_target(game_state, True)
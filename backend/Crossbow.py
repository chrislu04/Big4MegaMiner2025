import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name

class Crossbow(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState):
        super().__init__(
            x, y,
            team_color,
            Constants.CROSSBOW_MAX_COOLDOWN,
            Constants.CROSSBOW_RANGE,
            Constants.CROSSBOW_DAMAGE,
            Constants.CROSSBOW_PRICE,
            game_state
        )

        self.name = select_tower_name('CR', self.team)
    
    def tower_activation(self, game_state: GameState):
        super().shoot_single_priority_target(game_state)
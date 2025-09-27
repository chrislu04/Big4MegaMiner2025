from Tower import Tower

class Crossbow(Tower):
    def __init__(self, x: int, y: int, team_color: str) -> None:
        super().__init__(self, x, y, team_color)

    def __update__(self, game_state: GameState) -> None:
        pass # TODO
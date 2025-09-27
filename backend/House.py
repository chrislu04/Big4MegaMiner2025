from Tower import Tower

class House(Tower):
    def __init__(self, x: int, y: int, team_color: str) -> None:
        super().__init__(self, x, y, team_color)

        self.max_cooldown = 10
        self.current_cooldown = self.max_cooldown

    def __update__(self, game_state: GameState) -> None:
        pass # TODO
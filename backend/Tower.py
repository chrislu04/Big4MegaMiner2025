class Tower(Entity):
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.x = x
        self.y = y
        # BALANCE: initial reload formula: encourange long-term planning, but not too much
        # BALANCE: don't let the initial reload time be zero
        #self.reload_turns_left = math.ceil(self.tower_type.reload_turns//2)
        self.kills = 0
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?

    def __update__(self, game_state: GameState) -> None:
        pass # Override this
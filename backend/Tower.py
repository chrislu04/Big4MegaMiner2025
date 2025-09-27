from Entity import Entity

class Tower(Entity):
    def __init__(self, x: int, y: int, team_color: str, cooldown: int) -> None:
        super().__init__(self, 20, x, y)
        self.cooldown = cooldown

        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?
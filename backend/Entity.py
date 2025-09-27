import Constants

# Probably going to store health and position

class Entity:
    def __int__(self, health: int, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.health = health
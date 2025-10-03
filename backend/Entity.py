import Constants

class Entity:
    def __init__(self, health: int, value : int, attak : int, x : int, y : int):
        self.x = x
        self.y = y
        self.health = health
        self.value = value ##Value is how much the entity cost
        self.attack_power = attak 
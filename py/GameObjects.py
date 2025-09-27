import Constants
import math


class PlayerBase:
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = Constants.PLAYER_BASE_INITIAL_HP
        self.x = x
        self.y = y
        self.mercenaries_queued = 0
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Player base team_color must be 'r' or 'b'") # TF2 reference?

class Enemy:
    def __init__(self, x: int, y: int) -> None:
        self.hp = Constants.ENEMY_INITIAL_HP
        self.x = x
        self.y = y
        self.attack_power = Constants.ENEMY_ATTACK_POWER

class Mercenary:
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = Constants.MERCENARY_INITIAL_HP
        self.x = x
        self.y = y
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?
        self.attack_power = Constants.MERCENARY_ATTACK_POWER

class EnemySpawner:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.reload_time_left = Constants.ENEMY_SPAWNER_RELOAD_TURNS

class TowerType:
    def __init__(self, name: str, damage: int, money_cost: int, tower_range: int, reload_turns: int) -> None:
        self.name = name
        self.damage = damage
        self.money_cost = money_cost
        self.tower_range = tower_range
        self.reload_turns = reload_turns

class Tower:
    def __init__(self, x: int, y: int, tower_type: TowerType, team_color: str) -> None:
        self.x = x
        self.y = y
        self.tower_type = tower_type
        # BALANCE: initial reload formula: encourange long-term planning, but not too much
        # BALANCE: don't let the initial reload time be zero
        #self.reload_turns_left = math.ceil(self.tower_type.reload_turns//2)
        self.kills = 0
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?

    def __update__(self, tower_type: TowerType) -> None:
        self.tower_type = tower_type
        if tower_type == 'house':
            print("HOUSE GENERATED MONEY")

class PlayerState:
    def __init__(self, team_color: str) -> None:
        if team_color in ['r','b']:
            self.team_color = team_color
        else:
            raise Exception("Player team_color must be 'r' or 'b'")
        team_name = None
        money = Constants.INITIAL_MONEY
        self.mercenaries = list()
        self.towers = list()

class GameState:
    def __init__(self) -> None:
        self.turns_progressed = 0
        self.victory = None
        self.map_width = None
        self.map_height = None
        self.player_state_r = PlayerState('r')
        self.player_state_b = PlayerState('b')
        self.map_tiles = dict() # (x,y) -> blue territory, red territory, path, etc.
        self.entity_lookup = dict() # (x,y) -> Mercenary, Enemy, Tower, Spawner, etc.
        self.enemies = list()
        self.enemy_spawners = list()

TOWER_TYPES = dict()
TOWER_TYPES["crossbow"] = TowerType(name="crossbow", damage=3,  money_cost=2, tower_range=2, reload_turns=2)
TOWER_TYPES["cannon"]   = TowerType(name="cannon",   damage=20, money_cost=5, tower_range=2, reload_turns=4)
TOWER_TYPES["minigun"]  = TowerType(name="minigun",  damage=1,  money_cost=4, tower_range=2, reload_turns=1)
TOWER_TYPES["house"]    = TowerType(name="house",    damage=0,  money_cost=3, tower_range=0, reload_turns=6)

Tower(1, 1, 'house', 'r')
import math
import time
import traceback
import subprocess
import resource
import sys
import json
import copy

# ---------- GAME DATA STRUCTURES ----------

class PlayerBase:
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = PLAYER_BASE_INITIAL_HP
        self.x = x
        self.y = y
        self.mercenaries_queued = 0
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Player base team_color must be 'r' or 'b'") # TF2 reference?

class Enemy:
    def __init__(self, x: int, y: int) -> None:
        self.hp = ENEMY_INITIAL_HP
        self.x = x
        self.y = y
        self.attack_power = ENEMY_ATTACK_POWER

class Mercenary:
    def __init__(self, x: int, y: int, team_color: str) -> None:
        self.hp = MERCENARY_INITIAL_HP
        self.x = x
        self.y = y
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?
        self.attack_power = MERCENARY_ATTACK_POWER

class EnemySpawner:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.reload_time_left = ENEMY_SPAWNER_RELOAD_TURNS

class TowerType:
    def __init__(self, name: str, damage: int, money_cost: int, tower_range: int, reload_turns: int, health: int) -> None:
        self.name = name
        self.damage = damage
        self.money_cost = money_cost
        self.tower_range = tower_range
        self.reload_turns = reload_turns
        self.health = health

class Tower:
    def __init__(self, x: int, y: int, tower_type: TowerType, team_color: str) -> None:
        self.x = x
        self.y = y
        self.tower_type = tower_type
        # BALANCE: initial reload formula: encourange long-term planning, but not too much
        # BALANCE: don't let the initial reload time be zero
        self.reload_turns_left = math.ceil(self.tower_type.reload_turns//2)
        self.kills = 0
        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Mercenary team_color must be 'r' or 'b'") # TF2 reference?

class PlayerState:
    def __init__(self, team_color: str) -> None:
        if team_color in ['r','b']:
            self.team_color = team_color
        else:
            raise Exception("Player team_color must be 'r' or 'b'")
        team_name = None
        builder_count = 1
        money = INITIAL_MONEY
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

# ---------- CONSTANTS ----------

# BALANCE: tweaking these numbers will make or break game balance
TOWER_TYPES = dict()
TOWER_TYPES["crossbow"] = TowerType(name="crossbow", damage=3,  money_cost=2, Tower_range=2, reload_turns=2, health=100)
TOWER_TYPES["cannon"]   = TowerType(name="cannon",   damage=20, money_cost=5, Tower_range=2, reload_turns=4, health=100)
TOWER_TYPES["minigun"]  = TowerType(name="minigun",  damage=1,  money_cost=4, Tower_range=2, reload_turns=1, health=100)
TOWER_TYPES["house"]    = TowerType(name="house",    damage=0,  money_cost=3, Tower_range=0, reload_turns=6, health=100)
INITIAL_MONEY: int = 3
HOUSE_MONEY_PRODUCED: int = 1
ENEMY_INITIAL_HP: int = 70
ENEMY_ATTACK_POWER: int = 10 # TODO: increase this over time?
MERCENARY_INITIAL_HP: int = 70
MERCENARY_ATTACK_POWER: int = 10
ENEMY_SPAWNER_RELOAD_TURNS: int = 10
BUILDER_PRICES: list = [4,8,16,32,64] # BALANCE: exploration/exploitation tradeoff, don't let players snowball too quickly
MAX_BUILDERS = len(BUILDER_PRICES) + 1
PLAYER_BASE_INITIAL_HP = 200

# ---------- ACTION VALIDATION & APPLICATION FUNCTIONS ----------

BUILDER_ACTION_TYPES = {"build","destroy","nothing"}

def builder_action_is_valid(game_state: GameState, builder_action: dict, team_color: str) -> bool:
    try:
        target = (builder_action["target_x"],builder_action["target_y"])
        match builder_action["action_type"]:
            case "build":
                # can only build in own territory
                try:
                    match game_state.map_tiles[target]:
                        case "blue territory":
                            if team_color != 'b': return False
                        case "red territory":
                            if team_color != 'r': return False
                        case _: return False
                except KeyError:
                    return False
                # can't build if something is in the way
                if target in game_state.entity_lookup.keys(): return False
                # can't build if there's not enough money
                match team_color:
                    case 'b': money = game_state.player_state_b.money
                    case 'r': money = game_state.player_state_r.money
                    case _:
                        print("We got the team color wrong. This is NOT the agent's fault.")
                        return False
                try:
                    if money < TOWER_TYPES[builder_action["tower_type"]].money_cost: return False
                except KeyError:
                    return False
            case "destroy":
                # can only destroy tower in own territory
                try:
                    match game_state.map_tiles[target]:
                        case "blue_territory":
                            if team_color != 'b': return False
                        case "red_territory":
                            if team_color != 'r': return False
                        case _: return False
                except KeyError:
                    return False
                # can't destroy tower if there is nothing at the target position
                if target not in game_state.entity_lookup.keys(): return False
                # can't destroy tower if there is something other than a tower at the target position
                if not game_state.entity_lookup[target] is Tower: return False
            case "nothing": return True
            case _: return False
    except KeyError:
        return False
    return True

def apply_builder_action(game_state: GameState, builder_action: dict, team_color: str) -> GameState:
    player_state = None
    match team_color:
        case 'b': game_state.player_state_b
        case 'r': game_state.player_state_r
        case _: raise Exception("Invalid team color")
    match builder_action["action_type"]:
        case "build":
            new_tower = Tower(
                builder_action["target_x"],
                builder_action["target_y"],
                TOWER_TYPES[builder_action["tower_type"]],
                team_color
            )
            player_state.towers.append(new_tower)
            game_state.entity_lookup[(builder_action["target_x"],builder_action["target_y"])] = new_tower
        case "destroy":
            game_state.entity_lookup.pop((builder_action["target_x"],builder_action["target_y"]))
            player_state.towers.remove(tower) # TODO: need some sort of UID system
        case "nothing":
            pass

# ---------- CORE GAME LOOP ----------

def init_game_state() -> GameState:
    gs = GameState()
    map_data = open("map.txt","r").readlines()
    gs.map_width = len(map_data[0])
    gs.map_height = len(map_data)
    for y in map_data:
        for x in y:
            match char:
                case 'b':
                    gs.map_tiles[(x,y)] = 'blue_territory'
                case 'B':
                    gs.map_tiles[(x,y)] = 'blue_territory'
                    gs.entity_lookup[(x,y)] = PlayerBase(x,y,'b')
                case 'r':
                    gs.map_tiles[(x,y)] = 'red_territory'
                case 'R':
                    gs.map_tiles[(x,y)] = 'red_territory'
                    gs.entity_lookup[(x,y)] = PlayerBase(x,y,'r')
                case '0':
                    gs.map_tiles[(x,y)] = 'path'
                case 'S':
                    spawner = Enemy_Spawner(x,y)
                    gs.Enemy_Spawners.append(spawner)
                case ' ':
                    pass
                case '\n':
                    pass
                case _:
                    raise Exception(f"Invalid symbol in map file")

def handle_builder_turn(process_r: subprocess.Popen, process_b: subprocess.Popen, game_state: GameState) -> GameState:
    return GameState()

def set_resource_limits():
    resource.setrlimit(resource.RLIMIT_AS, (4000000000, 4000000000)) # max 4 Gigabytes heap memory allocated
    resource.setrlimit(resource.RLIMIT_NOFILE, (0, 0))               # can't access any files

def open_subprocess_script(script_name: str) -> subprocess.Popen:
    try:
        # most security settings for subprocesses are only available on Linux
        # tournament will be run on a Linux machine, to restrict cheating
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            user=65534, # run as unpriveleged "nobody" user
            universal_newlines=True,
            preexec_fn=set_resource_limits
        )
    except AttributeError as e:
        # fallback to Windows-compatible subprocess: Windows users need the ability to test their code!
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
    return process

def run_game() -> None:
    print(f'\n--RUNNING GAME SERVER-- {time.localtime()}\n')
    game_state = init_game_state()
    process_b = None
    process_r = None
    try:
        process_b = open_subprocess_script("agent_b.py")
    except Exception as e:
        print("Failed to open subprocess for blue player:")
        traceback.print_exc() # TODO: find more edge cases here by testing on different devices
        process_b = None
    try:
        process_r = open_subprocess_script("agent_r.py")
    except Exception as e:
        print("Failed to open subprocess for red player:")
        traceback.print_exc() # TODO: find more edge cases here by testing on different devices
        process_r = None
    
    if process_b == None and process_r == None:
        print("Failed to open subprocess for both players. Both players are disqualified!")
    elif process_b == None:
        print("Failed to open subprocess for blue player. Red player wins!")
    elif process_r == None:
        print("Failed to open subprocess for red player. Blue player wins!")
    else:

        while game_state.victory == None:
            pass

# ---------- MAIN PROGRAM ENTRY POINT ----------

visualizer_output = None
if __name__ == "__main__":
    with open("agent_r","r") as ar: open("agent_b","w").writelines(ar.readlines()) # TODO: remove this line later: it's just for testing
    visualizer_output = open("visualizer.out","w")
    run_game()
    visualizer_output.close()
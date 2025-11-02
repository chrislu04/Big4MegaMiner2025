import json
import subprocess
from pathlib import Path
from Utils import log_msg
import Constants

# GameState and related imports
from GameState import GameState
from Mercenary import Mercenary
from Demon import Demon
from Cannon import Cannon
from Crossbow import Crossbow
from Minigun import Minigun
from House import House
from DemonSpawner import DemonSpawner

# AI Action and related imports
from AIAction import AIAction
from BuildPhase import build_tower_phase
from BuyMercenaryPhase import buy_mercenary_phase
from WorldUpdatePhase import world_update_phase


# Contain the GameState, and run logic for progressing turns
class Game:
    def __init__(
        self,
        # Path to map JSON file, which has tile locations, base locations, etc
        map_json_file_path: str
    ):

        map_json_data = json.load(open(map_json_file_path, 'r'))
        self.game_state = GameState(map_json_data)


    # Perform updates to GameState based on two AI Actions
    def run_turn(self, action_r: AIAction, action_b: AIAction):
        
        log_msg(f"-- TURN: {Constants.MAX_TURNS - self.game_state.turns_remaining}, REMAINING TURNS: {self.game_state.turns_remaining}--")
        buy_mercenary_phase(self.game_state, action_r, action_b)
        build_tower_phase(self.game_state, action_r, action_b)
        world_update_phase(self.game_state)
        self.game_state.turns_remaining -= 1
        log_msg("")


    # Converts the game state to a json string that'll be usable by the AI's (and the visualizer later...)
    def game_state_to_json(self) -> str:

        dict_player_base_r : dict = {
            "Team" : self.game_state.player_base_r.team,
            "Health" : self.game_state.player_base_r.health,
            "x" : self.game_state.player_base_r.x,
            "y" : self.game_state.player_base_r.y
        }

        dict_player_base_b : dict = {
            "Team" : self.game_state.player_base_b.team,
            "Health" : self.game_state.player_base_b.health,
            "x" : self.game_state.player_base_b.x,
            "y" : self.game_state.player_base_b.y
        }
        # Changing the entity grid to a bunch of strings
        dict_entity_grid = []
        for y in range(len(self.game_state.entity_grid)):
            row = []
            for x in range(len(self.game_state.entity_grid[0])):
                if self.game_state.entity_grid[y][x] == None:
                    row.append(None)
                elif self.game_state.entity_grid[y][x] == "base":
                    row.append("base")
                elif isinstance(self.game_state.entity_grid[y][x], Mercenary):
                    row.append("Mercenary")
                elif isinstance(self.game_state.entity_grid[y][x], House):
                    row.append("House")
                elif isinstance(self.game_state.entity_grid[y][x], Cannon):
                    row.append("Cannon")
                elif isinstance(self.game_state.entity_grid[y][x], Crossbow):
                    row.append("Crossbow")
            dict_entity_grid.append(row)

        # Converting mercenarys to dicts in merc list
        dict_mercenary = []
        for merca in self.game_state.mercs:
            if isinstance(merca, Mercenary):
                merc_dict : dict = {
                    "Mercenary" : {
                        "Team" : merca.team,
                        "x" : merca.x,
                        "y" : merca.y,
                        "health" : merca.health,
                        "state" : merca.state
                    }
                }
                dict_mercenary.append(merc_dict)

        dict_towers = []
        for tow in self.game_state.towers:
            tower_name = ""
            if isinstance(tow, Crossbow):
                tower_name = "Crossbow"
            elif isinstance(tow, House):
                tower_name = "House"
            elif isinstance(tow, Cannon):
                tower_name = "Cannon"
            elif isinstance(tow, Minigun):
                tower_name = "Minigun"
                
            tow_dict : dict = {
                "Type" : tower_name, # Getting the type doesn't work
                "Team" : tow.team,
                "x" : tow.x,
                "y" : tow.y,
                "AimAngle" : tow.angle * 57.2958 ##Convert radians to degrees
            }
            dict_towers.append(tow_dict)

        dict_demons = []
        for dem in self.game_state.demons:
            if isinstance(dem, Demon):
                dem_dict = {
                    "Team" : dem.target_team,
                    "x" : dem.x,
                    "y" : dem.y,
                    "health" : dem.health,
                    "state" : dem.state
                }
                dict_demons.append(dem_dict)

        data : dict = {
            "Victory" : self.game_state.victory,
            "TurnsRemaining" : self.game_state.turns_remaining,

            "PlayerBaseR" : dict_player_base_r,
            "PlayerBaseB" : dict_player_base_b,

            "FloorTiles" : self.game_state.floor_tiles,
            "EntityGrid" : dict_entity_grid,
            "Towers" : dict_towers,
            "Mercenaries" : dict_mercenary,
            "Demons" : dict_demons
        } 

        json_string : str = json.dumps(data, indent=4)

        return json_string
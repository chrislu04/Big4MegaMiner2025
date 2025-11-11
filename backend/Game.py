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
from ProvokeDemonsPhase import provoke_demons_phase


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
        
        log_msg(f"-- TURN: {Constants.MAX_TURNS - self.game_state.turns_remaining}, REMAINING TURNS: {self.game_state.turns_remaining}, BLUE: ${self.game_state.money_b}, RED: {self.game_state.money_r} $--")
        buy_mercenary_phase(self.game_state, action_r, action_b)
        build_tower_phase(self.game_state, action_r, action_b)
        provoked_demons = provoke_demons_phase(self.game_state, action_r, action_b)
        world_update_phase(self.game_state, provoked_demons)
        self.game_state.turns_remaining -= 1
        log_msg("")


    # Converts the game state to a json string that'll be usable by the AI's
    def game_state_to_json(self) -> str:

        dict_player_base_r : dict = {
            "Team" : self.game_state.player_base_r.team,
            "Health" : self.game_state.player_base_r.health,
            "Money" : self.game_state.money_r,
            "x" : self.game_state.player_base_r.x,
            "y" : self.game_state.player_base_r.y
        }

        dict_player_base_b : dict = {
            "Team" : self.game_state.player_base_b.team,
            "Health" : self.game_state.player_base_b.health,
            "Money" : self.game_state.money_b,
            "x" : self.game_state.player_base_b.x,
            "y" : self.game_state.player_base_b.y
        }

        # Changing the entity grid to a bunch of strings
        list_entity_grid = []
        for y in self.game_state.entity_grid:
            row = []
            for ent_at_xy in y:
                if ent_at_xy is None:
                    row.append('')
                else:
                    row.append(ent_at_xy.name)
            list_entity_grid.append(row)

        # Converting mercenarys to dicts in merc list
        list_mercenary = []
        for merc in self.game_state.mercs:
            merc_dict : dict = {
                "Name" : merc.name,
                "Team" : merc.team,
                "x" : merc.x,
                "y" : merc.y,
                "Health" : merc.health,
                "State" : merc.state
            }
            list_mercenary.append(merc_dict)

        list_towers = []
        for tow in self.game_state.towers:
            tower_type = ""
            if isinstance(tow, Crossbow):
                tower_type = "Crossbow"
            elif isinstance(tow, House):
                tower_type = "House"
            elif isinstance(tow, Cannon):
                tower_type = "Cannon"
            elif isinstance(tow, Minigun):
                tower_type = "Minigun"
            
            target_list = []

            for target in tow.targets:
                target_list.append(target)

            tow_dict : dict = {
                "Name" : tow.name,
                "Type" : tower_type,
                "Team" : tow.team,
                "x" : tow.x,
                "y" : tow.y,
                "Targets" : target_list
                # "AimAngle" : tow.angle * 57.2958 # Convert radians to degrees
            }
            list_towers.append(tow_dict)

        list_demons = []
        for dem in self.game_state.demons:
            if isinstance(dem, Demon):
                dem_dict = {
                    "Name" : dem.name,
                    "Team" : dem.target_team,
                    "x" : dem.x,
                    "y" : dem.y,
                    "Health" : dem.health,
                    "State" : dem.state
                }
                list_demons.append(dem_dict)

        data : dict = {
            "Victory" : self.game_state.victory,
            "TurnsRemaining" : self.game_state.turns_remaining,
            "CurrentTurn" : Constants.MAX_TURNS - self.game_state.turns_remaining,

            "PlayerBaseR" : dict_player_base_r,
            "PlayerBaseB" : dict_player_base_b,
            "RedTeamMoney" : self.game_state.money_r,
            "BlueTeamMoney" : self.game_state.money_b,

            "FloorTiles" : self.game_state.floor_tiles,
            "EntityGrid" : list_entity_grid,
            "Towers" : list_towers,
            "Mercenaries" : list_mercenary,
            "Demons" : list_demons
        } 

        json_string : str = json.dumps(data)

        return json_string
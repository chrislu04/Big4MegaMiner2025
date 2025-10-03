# import math
# import time
# import traceback
# import subprocess
# #import resource
# import sys
import json
#import copy
from GameState import GameState
from AIAction import AIAction
from BuildPhase import build_tower_phase ## This is crazy lol python weird - Dorian
from BuyMercenaryPhase import buy_mercenary_phase
from WorldUpdatePhase import world_update_phase
import subprocess
from Mercenary import Mercenary
from Demon import Demon
from Cannon import Cannon
from Crossbow import Crossbow
from Minigun import Minigun
from House import House

class Game:
    def __init__(self, agent_path_1 = "", agent_path_2 = ""):
        # Path to the Agent1.py file
        self.agent_path_1 : str = agent_path_1
        # Path to the Agent2.py file
        self.agent_path_2 : str = agent_path_2

        self.game_state : GameState = GameState("r",1,1) 

    ## Kind of useless??? 
    def reset(self):
        pass

    def run_turn(self, game_state = None):
        if game_state != None:
            self.game_state = game_state
        
        ## ----Get AI Actions---- ##
        ## First player turn
        try:
            ## This is an example of how we're sending the data to the ai's and how we're recieving them
            ## We're using subprocess to start the ai files, we're using check output to save the output (the print functions)
            AI_1_action = (subprocess.check_output(["python", self.AI_Path_1, self.game_state_to_json()])).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")

        ## Second player turn
        try:
            AI_2_action = (subprocess.check_output(["python", self.AI_Path_2, self.game_state_to_json()])).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
        
        ## an example on how to parse though actions and change the game state
        action_r : AIAction = self.decode_action(AI_1_action)
        action_b : AIAction = self.decode_action(AI_2_action)

        ##Call buy phase
        build_tower_phase(self.game_state, action_r, action_b)

        ##Get actions again for merc buy phase

        ## First player turn
        try:
            ## This is an example of how we're sending the data to the ai's and how we're recieving them
            ## We're using subprocess to start the ai files, we're using check output to save the output (the print functions)
            AI_1_action = (subprocess.check_output(["python", self.AI_Path_1, self.game_state_to_json()])).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
            
        ## Second player turn
        try:
            AI_2_action = (subprocess.check_output(["python", self.AI_Path_2, self.game_state_to_json()])).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
        
        action_r = self.decode_action(AI_1_action)
        action_b = self.decode_action(AI_2_action)

        ## call merc buy phase
        buy_mercenary_phase(self.game_state, action_r, action_b)
        ## ----Update game state with towers, and queues---- ##

        world_update_phase(self.game_state)

        ## ----Update the turn---- ##
        self.game_state.turns_progressed += 1

            
        

    ##---------------HELPERS-----------------##

    ## Converts the game state to a json string that'll be usable by the AI's (and the visualizer later...)
    def game_state_to_json(self) -> str:

        ## Changing the entity grid to a bunch of strings
        string_entity_grid = []
        for x in range(len(self.game_state.entity_grid)):
            row = []
            for y in range(len(self.game_state.entity_grid[0])):
                if self.game_state.entity_grid[x][y] == None:
                    row.append(None)
                elif self.game_state.entity_grid[x][y] == "base":
                    row.append("base")
                elif isinstance(self.game_state.entity_grid[x][y], Mercenary):
                    row.append("Mercenary")
                elif isinstance(self.game_state.entity_grid[x][y], House):
                    row.append("House")
                elif isinstance(self.game_state.entity_grid[x][y], Cannon):
                    row.append("Cannon")
                elif isinstance(self.game_state.entity_grid[x][y], Crossbow):
                    row.append("Crossbow")
            string_entity_grid.append(row)

        ## Converting mercenarys to dicts in merc list
        string_mercenary = []
        for merca in self.game_state.mercs:
            if isinstance(merca, Mercenary):
                merc_dict : dict = {
                    "Mercenary" : {
                        "Team" : "b",
                        "x" : merca.x,
                        "y" : merca.y,
                        "hp" : merca.health,
                        "state" : merca.state
                    }
                }
                string_mercenary.append(merc_dict)

        string_towers = []
        for tow in self.game_state.towers:
            tower_name = ""
            if isinstance(tow, Crossbow):
                tower_name = "Crossbow"
            tow_dict : dict = {
                "Type" : tower_name, # Getting the type doesn't work
                "x" : tow.x,
                "y" : tow.y,
            }
            string_towers.append(tow_dict)


        data : dict = {
            "TileGrid" : self.game_state.tile_grid,
            "EntityGrid" : string_entity_grid,
            "Towers" : string_towers,
            "Mercenaries" : string_mercenary,
            "Demons" : self.game_state.demons
        } 

        json_string : str = json.dumps(data, indent=4)


        return json_string

    def json_to_game_state(self):
        pass

    def load_ai_paths(self, path_one : str, path_two : str):
        self.AI_Path_1 = path_one
        self.AI_Path_2 = path_two
    
    ## Decodes whatever the ai file will sent into actually usable information,
    ## This is most likely to change later
    def decode_action(self, action : str) -> AIAction:
        action_string  : str = action.split(" ")
        ai_action : AIAction
    
        match action_string[0].strip().lower():
            case "build":
                ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], buy=True,) ##Making a lot of bold assumptions here
            case "destroy":                                                                                     
                ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], destory=True,) 
            case "queue":
                ai_action = AIAction(0, 0, queue_direction=action_string[3], queue=True,) ## Queuing wouldn't need an x or y, ai would just add a direction as the params

        return ai_action
                

    ##---------------ACTIONS-----------------##

    ## Checks if the player can build a tower at this location
    ## True if the action is within the team_color's terrirtory, it doesnt overlape with towers
    ## False if it isn't within the team_color's terrirtoty, it does overlap with other towers
    def can_build(self, x,  y, team_color) -> bool:
        return False
    
    ## Checks if the player can destroy a tower at this location
    ## True if the action is within the team_color's terrirtory
    ## False if it isn't within the team_color's terrirtoty
    def can_destroy(self, x, y, team_color) -> bool:
        return False

    ## Builds a tower at x and y, tower will be of tower_type
    def build(self, x, y, tower_type) -> None:
        pass
    
    ## Destroys a tower in x and y
    def destroy(self, x, y) -> None:
        pass
    
    ## Queues a mercenary, unsure of 
    def queue(self, x, y):
        pass



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
from BuildPhase import build_tower_phase ## This is dumb, move it into game once finished
import subprocess

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

    def run(self):
        ## Assuming here that the game state has been initilaized

        ## If the game has been running for 1000 turns or over, end the game
        while self.game_state.turns_progressed < 1000:
        
            ## ----Get AI Actions---- ##

            ## First player turn
            try:
                ## This is an example of how we're sending the data to the ai's and how we're recieving them
                ## We're using subprocess to start the ai files, we're using check output to save the output (the print functions)
                AI_1_action = (subprocess.check_output(["python", self.AI_Path_1, self.save_game_State_to_json()])).decode('utf-8')
            except subprocess.CalledProcessError as e:
                print(f"Command failed with return code {e.returncode}")
            
            ## Second player turn
            try:
                AI_2_action = (subprocess.check_output(["python", self.AI_Path_2, self.save_game_State_to_json()])).decode('utf-8')
            except subprocess.CalledProcessError as e:
                print(f"Command failed with return code {e.returncode}")
            
            ## an example on how to parse though actions and change the game state
            action_r : AIAction = self.decode_action(AI_1_action)
            action_b : AIAction = self.decode_action(AI_2_action)
            ## ----Update game state with towers, and queues---- ##

            ##Call buy phase
            build_tower_phase(self.game_state, action_r, action_b)

            ##Get actions again for merc buy phase


            ## call merc buy phase
            
            ## ----Update game state with towers, and queues---- ##


            ## ----Update the turn---- ##
            self.game_state.turns_progressed

            
        

    ##---------------HELPERS-----------------##

    def save_game_State_to_json(self) -> str:
        data = json.dumps(self.game_state.map_tiles)
        return data

    def load_game_state_from_json(self):
        pass

    def load_ai_paths(self, path_one : str, path_two : str):
        self.AI_Path_1 = path_one
        self.AI_Path_2 = path_two
    
    ## Decodes whatever the ai file will sent into actually usable information,
    ## This is most likely to change later
    def decode_action(self, action : str) -> AIAction:
        action_string  : str = action.split(" ")
        ai_action : AIAction

        match action_string[0].lower():
            case "build":
                ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], buy=True,) ##Making a lot of bold assumptions here
            case "destroy":                                                                                     
                ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], destory=True,) 
            case "queue":
                ai_action = AIAction(0, 0, action_string[3], queue=True,) ## Queuing wouldn't need an x or y, ai would just add a direction as the params

    
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



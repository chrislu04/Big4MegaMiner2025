import json
from GameState import GameState
from AIAction import AIAction
from BuildPhase import build_tower_phase
from BuyMercenaryPhase import buy_mercenary_phase
from WorldUpdatePhase import world_update_phase
import subprocess
from Mercenary import Mercenary
from Demon import Demon
from Cannon import Cannon
from Crossbow import Crossbow
from Minigun import Minigun
from House import House
from pathlib import Path
from DemonSpawner import DemonSpawner

class Game:
    def __init__(self, agent_path_1 = "", agent_path_2 = ""):
        # Path to the Agent1.py file
        self.agent_path_1 : str = agent_path_1
        # Path to the Agent2.py file
        self.agent_path_2 : str = agent_path_2

        self.game_state : GameState = GameState("r",1,1)
        self.game_state.demon_spawners.append(DemonSpawner(10, 5, "b"))
        self.game_state.demon_spawners.append(DemonSpawner(12, 5, "r"))

        self.game_json_file_path = str(Path(__file__).parent.resolve()) + '/data/game_state_json.txt'

        # self.game_json_file_path = Path(self.game_json_file_path).resolve()

    # Kind of useless??? 
    def reset(self):
        pass

    def run_turn(self, game_state = None):
        if game_state != None:
            self.game_state = game_state
        
        self.game_state.money_b += 20
        self.game_state.money_r += 20
        
        self.game_state.current_phase = "tower build"

        with open(self.game_json_file_path, 'w') as outp:
                outp.write(self.game_state_to_json())

        # ----Getting AI Actions Example---- ##
        # This is an example of how we're sending the data to the ai's and how we're recieving them
        # We're using subprocess to start the ai files, and getting thier outputs (the print functions)

        # First player turn
        try:
            process = subprocess.run(["python", self.AI_Path_1, self.game_json_file_path], shell=True,capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
        
        # print(process.stdout.decode('utf-8'))
        action_r : AIAction = self.decode_action(process.stdout.decode('utf-8'))
        # print(action_r)
        # Second player turn
        try:
            process = subprocess.run(["python", self.AI_Path_2, self.game_json_file_path], shell=True,capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
        
        action_b : AIAction = self.decode_action(process.stdout.decode('utf-8'))

        build_tower_phase(self.game_state, action_r, action_b)

        ##Get actions again for merc buy phase

        self.game_state.current_phase = "mercs buy"

        with open(self.game_json_file_path, 'w') as outp:
                outp.write(self.game_state_to_json())

        try:
            process = subprocess.run(["python", self.AI_Path_1, self.game_json_file_path], shell=True,capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
        
        action_r = self.decode_action(process.stdout.decode('utf-8'))

        try:
            process = subprocess.run(["python", self.AI_Path_2, self.game_json_file_path], shell=True,capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
        
        action_b = self.decode_action(process.stdout.decode('utf-8'))

        # call merc buy phase
        buy_mercenary_phase(self.game_state, action_r, action_b)
        # ----Update game state with towers, and queues---- ##

        world_update_phase(self.game_state)

        # ----Update the turn---- ##

        self.game_state.turns_progressed += 1
        
        with open(self.game_json_file_path, 'w') as outp:
                outp.write(self.game_state_to_json())



    ##---------------HELPERS-----------------##

    # Converts the game state to a json string that'll be usable by the AI's (and the visualizer later...)
    def game_state_to_json(self) -> str:

        string_player_base_r : dict = {
            "Team" : self.game_state.player_base_r.team,
            "Health" : self.game_state.player_base_r.health,
            "Money" : self.game_state.money_r,
            "x" : self.game_state.player_base_r.x,
            "y" : self.game_state.player_base_r.y
        }

        string_player_base_b : dict = {
            "Team" : self.game_state.player_base_b.team,
            "Health" : self.game_state.player_base_b.health,
            "Money" : self.game_state.money_b,
            "x" : self.game_state.player_base_b.x,
            "y" : self.game_state.player_base_b.y
        }
        # Changing the entity grid to a bunch of strings
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

        # Converting mercenarys to dicts in merc list
        string_mercenary = []
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
                string_mercenary.append(merc_dict)

        string_towers = []
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
            string_towers.append(tow_dict)

        string_demons = []
        for dem in self.game_state.demons:
            if isinstance(dem, Demon):
                dem_dict = {
                    "Team" : dem.target_team,
                    "x" : dem.x,
                    "y" : dem.y,
                    "health" : dem.health,
                    "state" : dem.state
                }
                string_demons.append(dem_dict)

        data : dict = {
            "Victory" : self.game_state.victory,
            "TurnsProgressed" : self.game_state.turns_progressed,
            "CurrentPhase" : self.game_state.current_phase,

            "RedPlayer" : string_player_base_r,
            "BluePlayer" : string_player_base_b,

            "TileGrid" : self.game_state.tile_grid,
            "EntityGrid" : string_entity_grid,
            "Towers" : string_towers,
            "Mercenaries" : string_mercenary,
            "Demons" : string_demons
        } 

        json_string : str = json.dumps(data, indent=4)

        # with open('backend/test.json', 'wb') as outp:
        #     pickle.dump(json_string, outp, pickle.HIGHEST_PROTOCOL)

        return json_string


    def load_ai_paths(self, path_one : str, path_two : str):
        self.AI_Path_1 = path_one
        self.AI_Path_2 = path_two
    
    # Decodes whatever the ai file will sent into actually usable information,
    # This is most likely to change later
    def decode_action(self, action : str) -> AIAction:
        
        action_string  : str = action.split(" ")
        ai_action : AIAction = AIAction(0,0) # Base case, this action doesn't do anything
    
        match action_string[0].strip().lower():
            case "build":
                ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], buy=True,) ##Making a lot of bold assumptions here
            case "destroy":                                                                                     
                ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], destory=True,) 
            case "queue":
                ai_action = AIAction(0, 0, queue_direction=action_string[3], queue=True,) # Queuing wouldn't need an x or y, ai would just add a direction as the params
        
        return ai_action
                
    def change_data_directory(self, directory : str):
        self.game_json_file_path = directory + "/data/game_state_json.txt"

    def make_blank_game(self):
        
        with open(self.game_json_file_path, 'w') as outp:
            outp.write(self.game_state_to_json())

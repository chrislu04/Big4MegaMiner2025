# This script defines the PPO (Proximal Policy Optimization) agent that plays the MegaMiner game.
# It loads a pre-trained PPO model and uses it to decide on actions during the game.
# This script is designed to be run as a separate process by the game engine.

import json
import numpy as np
import sys
from pathlib import Path

# Add the backend directory to the Python path to import game constants.
# This is necessary for the observation conversion function.
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
import Constants

class AIAction:
    """
    Represents one turn of actions in the game.
    This class is a simplified copy from the game's backend to make the agent self-contained.
    It allows the agent to structure its chosen action in a way the game engine understands.
    """
    def __init__(
        self,
        action: str,
        x: int,
        y: int,
        tower_type: str = "",
        merc_direction: str = ""
    ):
        self.action = action.lower().strip()
        self.x = x
        self.y = y
        self.tower_type = tower_type.strip()
        self.merc_direction = merc_direction.upper().strip()

    def to_dict(self):
        """Converts the action to a dictionary."""
        return {
            'action': self.action, 'x': self.x, 'y': self.y,
            'tower_type': self.tower_type, 'merc_direction': self.merc_direction
        }

    def to_json(self):
        """Serializes the action to a JSON string, which is sent to the game engine."""
        return json.dumps(self.to_dict())

def _convert_state_to_obs(game_state: dict, team_color: str) -> np.ndarray:
    """
    Converts the JSON game state into the same flattened observation
    that the training environment's _get_obs() produces, after a
    FlattenObservation wrapper (map + vector concatenated).
    """

    # Map size from JSON
    map_w = len(game_state['FloorTiles'][0])
    map_h = len(game_state['FloorTiles'])

    MAX_MAP_WIDTH = 50
    MAX_MAP_HEIGHT = 50

    is_red_agent = (team_color == "r")

    # --- Map tensor (H, W, 7) ---
    obs_map = np.zeros((MAX_MAP_HEIGHT, MAX_MAP_WIDTH, 7), dtype=np.float32)
    map_view = obs_map[:map_h, :map_w, :]

    # =========
    # Channel 0: Terrain (path / my territory / opp territory)
    # =========
    my_territory_char = 'r' if is_red_agent else 'b'
    opp_territory_char = 'b' if is_red_agent else 'r'

    for y, row in enumerate(game_state['FloorTiles']):
        for x, tile in enumerate(row):
            t = tile.lower()
            if t == 'p':
                map_view[y, x, 0] = 1
            elif t == my_territory_char:
                map_view[y, x, 0] = 2
            elif t == opp_territory_char:
                map_view[y, x, 0] = 3

    # =========
    # Towers, Mercs, Demons, Bases
    # =========

    # For tower meta
    tower_type_map = {"crossbow": 1, "cannon": 2, "minigun": 3, "house": 4}
    tower_cooldown_max = {
        "HOUSE": Constants.HOUSE_MAX_COOLDOWN,
        "CANNON": Constants.CANNON_MAX_COOLDOWN,
        "MINIGUN": Constants.MINIGUN_MAX_COOLDOWN,
        "CROSSBOW": Constants.CROSSBOW_MAX_COOLDOWN,
    }

    # For DPT heatmaps (my damage vs opp damage on path tiles)
    my_dpt_map = np.zeros((map_h, map_w), dtype=np.float32)
    opp_dpt_map = np.zeros((map_h, map_w), dtype=np.float32)

    tower_damage_map = {
        "CANNON":   Constants.CANNON_DAMAGE,
        "MINIGUN":  Constants.MINIGUN_DAMAGE,
        "CROSSBOW": Constants.CROSSBOW_DAMAGE,
    }
    tower_range_map = {
        "CANNON":   Constants.CANNON_RANGE,
        "MINIGUN":  Constants.MINIGUN_RANGE,
        "CROSSBOW": Constants.CROSSBOW_RANGE,
    }

    # --- Towers ---
    for t in game_state['Towers']:
        tx, ty = t['x'], t['y']
        t_name = t['Name'].upper()        # e.g., "CANNON"
        t_type = t['Type'].lower()        # e.g., "Cannon" in JSON
        t_team = t['Team']                # 'r' or 'b'

        my_team = (is_red_agent and t_team == 'r') or ((not is_red_agent) and t_team == 'b')

        map_view[ty, tx, 1] = 1                 # entity type: tower
        # Health on towers is stored in backend, but may not be in JSON; default to 1 if missing
        health = t.get('Health', 1.0)
        map_view[ty, tx, 2] = health
        map_view[ty, tx, 3] = 1 if my_team else -1
        map_view[ty, tx, 4] = tower_type_map.get(t_type, 0)

        # Damage-per-tile heatmap (only offensive towers with defined damage/range)
        if t_name in tower_damage_map:
            damage = tower_damage_map[t_name]
            rng = tower_range_map[t_name]
            max_cd = tower_cooldown_max.get(t_name, 1)
            damage_per_turn = damage / max_cd if max_cd > 0 else damage

            for dy in range(-rng, rng + 1):
                for dx in range(-rng, rng + 1):
                    ny, nx = ty + dy, tx + dx
                    if 0 <= ny < map_h and 0 <= nx < map_w:
                        # only apply on path tiles (terrain channel == 1)
                        if map_view[ny, nx, 0] == 1:
                            if my_team:
                                my_dpt_map[ny, nx] += damage_per_turn
                            else:
                                opp_dpt_map[ny, nx] += damage_per_turn

    # Apply DPT maps to channels 5 and 6
    map_view[:, :, 5] = my_dpt_map
    map_view[:, :, 6] = opp_dpt_map

    # --- Mercenaries ---
    for m in game_state['Mercenaries']:
        mx, my = int(m['x']), int(m['y'])
        m_team = m['Team']
        my_team = (is_red_agent and m_team == 'r') or ((not is_red_agent) and m_team == 'b')

        map_view[my, mx, 1] = 2  # entity type: merc
        if Constants.MERCENARY_INITIAL_HEALTH > 0:
            map_view[my, mx, 2] = m['Health'] / Constants.MERCENARY_INITIAL_HEALTH
        else:
            map_view[my, mx, 2] = 0.0
        map_view[my, mx, 3] = 1 if my_team else -1

    # --- Demons ---
    for d in game_state['Demons']:
        dx, dy = int(d['x']), int(d['y'])
        map_view[dy, dx, 1] = 3  # entity type: demon
        if Constants.DEMON_INITIAL_HEALTH > 0:
            map_view[dy, dx, 2] = d['Health'] / Constants.DEMON_INITIAL_HEALTH
        else:
            map_view[dy, dx, 2] = 0.0
        map_view[dy, dx, 3] = 0  # neutral

    # --- Bases ---
    base_r = game_state['PlayerBaseR']
    base_b = game_state['PlayerBaseB']
    my_base  = base_r if is_red_agent else base_b
    opp_base = base_b if is_red_agent else base_r

    # My base
    map_view[my_base['y'], my_base['x'], 1] = 4
    if Constants.PLAYER_BASE_INITIAL_HEALTH > 0:
        map_view[my_base['y'], my_base['x'], 2] = my_base['Health'] / Constants.PLAYER_BASE_INITIAL_HEALTH
    else:
        map_view[my_base['y'], my_base['x'], 2] = 0.0
    map_view[my_base['y'], my_base['x'], 3] = 1

    # Opp base
    map_view[opp_base['y'], opp_base['x'], 1] = 4
    if Constants.PLAYER_BASE_INITIAL_HEALTH > 0:
        map_view[opp_base['y'], opp_base['x'], 2] = opp_base['Health'] / Constants.PLAYER_BASE_INITIAL_HEALTH
    else:
        map_view[opp_base['y'], opp_base['x'], 2] = 0.0
    map_view[opp_base['y'], opp_base['x'], 3] = -1

    # =========
    # Vector features (10,)
    # =========
    my_money  = game_state['RedTeamMoney'] if is_red_agent else game_state['BlueTeamMoney']
    opp_money = game_state['BlueTeamMoney'] if is_red_agent else game_state['RedTeamMoney']
    my_base_health  = my_base['Health']
    opp_base_health = opp_base['Health']
    turns_remaining = game_state['TurnsRemaining']

    # Tower prices per team from JSON
    tower_prices = game_state['TowerPricesR'] if is_red_agent else game_state['TowerPricesB']
    House_Cost    = tower_prices['House']
    Crossbow_Cost = tower_prices['Crossbow']
    Cannon_Cost   = tower_prices['Cannon']
    Minigun_Cost  = tower_prices['Minigun']
    Church_Cost   = tower_prices['Church']

    vector_features = np.array([
        my_money, my_base_health,
        opp_money, opp_base_health,
        turns_remaining,
        House_Cost, Crossbow_Cost, Cannon_Cost, Minigun_Cost, Church_Cost
    ], dtype=np.float32)

    # Normalize exactly like env._get_obs
    vector_features[0] /= 100.0
    vector_features[1] /= (Constants.PLAYER_BASE_INITIAL_HEALTH or 1.0)
    vector_features[2] /= 100.0
    vector_features[3] /= (Constants.PLAYER_BASE_INITIAL_HEALTH or 1.0)
    vector_features[4] /= (Constants.MAX_TURNS or 1.0)
    vector_features[5:10] /= 100.0  # tower costs

    return {
            'map': obs_map,
            'vector': vector_features
        }

# Create a debug log file
DEBUG_LOG = Path(__file__).resolve().parent / "agent_debug.log"

def debug_log(msg):
    """Write debug messages to a file instead of stderr."""
    with open(DEBUG_LOG, "a") as f:
        f.write(f"{msg}\n")

class Agent:
    def initialize_and_set_name(self, initial_game_state: dict, team_color: str) -> str:
        debug_log("=== Agent Initialization ===")
        debug_log(f"Team color: {team_color}")
        
        self.team_color = team_color
        from stable_baselines3 import PPO
        
        model_path = Path(__file__).resolve().parent.parent / "training_copy" / "models" / "best_model" / "best_model.zip"
        #debug_log(f"Loading model from: {model_path}")
        try:
            self.model = PPO.load(model_path)
            #debug_log("Model loaded successfully.")
        except Exception as e:
            #debug_log(f"ERROR: Failed to load PPO model: {e}")
            raise
        
        return "Big Hero 4"
    
    def do_turn(self, game_state: dict) -> AIAction:
        #debug_log("=== Turn Start ===")
        
        observation = _convert_state_to_obs(game_state, self.team_color)
        #debug_log(f"Observation shape: {observation.shape}")
        
        #observation = observation.reshape(1, -1)
        #debug_log(f"Observation: {observation}")
        
        try:
            action_vector, _states = self.model.predict(observation, deterministic=True)
            #debug_log(f"Action vector: {action_vector}")
        except Exception as e:
            #debug_log(f"ERROR: Failed to predict: {e}")
            raise
        
        action_type_map = {0: "nothing", 1: "build", 2: "destroy"}
        tower_type_map = {0: "crossbow", 1: "cannon", 2: "minigun", 3: "house", 4: "church"}
        merc_dir_map = {0: "", 1: "N", 2: "S", 3: "E", 4: "W"}

        act_type, x, y, tower_type, merc_dir = action_vector

        ai_action = AIAction(
            action=action_type_map[act_type],
            x=int(x),
            y=int(y),
            tower_type=tower_type_map[tower_type],
            merc_direction=merc_dir_map[merc_dir]
        )
        debug_log(f"Action: {ai_action.to_dict()}")
        
        return ai_action

# -- DRIVER CODE (DO NOT ALTER) --
# This part of the script handles the communication with the game engine.
# It reads the game state from standard input and writes the agent's actions to standard output.
if __name__ == '__main__':
    # Determine team color from the first line of input.
    team_color = 'r' if input() == "--YOU ARE RED--" else 'b'
    
    # Read the initial game state.
    initial_state_json = ""
    while True:
        line = input()
        if line == "--END INITIAL GAME STATE--":
            break
        initial_state_json += line
    game_state_init = json.loads(initial_state_json)

    # Initialize the agent.
    agent = Agent()
    # The first output must be the agent's name.
    print(agent.initialize_and_set_name(game_state_init, team_color))
    # The second output is the action for the first turn.
    print(agent.do_turn(game_state_init).to_json())

    # Main game loop.
    while True:
        # Read the game state for the current turn.
        turn_state_json = ""
        while True:
            line = input()
            if line == "--END OF TURN--":
                break
            turn_state_json += line
        game_state_this_turn = json.loads(turn_state_json)
        # Output the agent's action for this turn.
        print(agent.do_turn(game_state_this_turn).to_json())
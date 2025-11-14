import gymnasium
import numpy as np
from gymnasium.spaces import Box, Dict, Discrete
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector, wrappers
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from Game import Game
from AIAction import AIAction
import Constants

def env(map_path):
    """
    The env function wraps the environment in declared wrappers.
    """
    internal_render_mode = "human"
    env = raw_env(render_mode=internal_render_mode, map_path=map_path)
    # This wrapper is required for environments with continuous action spaces
    # env = wrappers.ClipAction(env)
    # This wrapper is required for environments with discrete action spaces
    env = wrappers.AssertOutOfBoundsWrapper(env)
    # This wrapper is required for environments with multi-binary action spaces
    # env = wrappers.MultiBinaryCheck(env)
    # This wrapper is required for environments with a continuous observation space
    # env = wrappers.OrderEnforcingWrapper(env)
    return env

class raw_env(AECEnv):
    metadata = {
        "render_modes": ["human"],
        "name": "MegaMiner_v0",
        "is_parallelizable": True,
    }

    MAX_MAP_WIDTH = 50
    MAX_MAP_HEIGHT = 50

    def __init__(self, map_path, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        
        # The game map
        self.map_path = map_path
        self.game = Game(self.map_path)
        self.map_size = (len(self.game.game_state.floor_tiles[0]), len(self.game.game_state.floor_tiles))

        # PettingZoo setup
        self.agents = ["player_r", "player_b"]
        self.possible_agents = self.agents[:]
        self._agent_selector = agent_selector(self.agents)
        
        # Define action and observation spaces
        self._action_space_dict = self._create_action_space()
        self._observation_space_dict = self._create_observation_space()

        # Game state tracking
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}

        # Store actions between steps
        self.action_r = None
        self.action_b = None

    def observation_space(self, agent):
        return self._observation_space_dict

    def action_space(self, agent):
        return self._action_space_dict

    def _create_action_space(self):
        """
        Defines the action space for an agent.
        Uses MultiDiscrete for a flat vector of discrete choices.
        [action_type, x, y, tower_type, merc_direction]
        """
        return gymnasium.spaces.MultiDiscrete([
            3,  # action_type: 0=nothing, 1=build, 2=destroy
            self.MAX_MAP_WIDTH,  # x
            self.MAX_MAP_HEIGHT,  # y
            4,  # tower_type: 0=crossbow, 1=cannon, 2=minigun, 3=house
            5   # merc_direction: 0="", 1=N, 2=S, 3=E, 4=W
        ])

    def _create_observation_space(self):
        """
        Defines the observation space for an agent for a flat MLP model.
        """
        map_shape = (self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 7)
        vector_size = 5
        
        # Flatten the map and concatenate with the vector features
        total_obs_size = np.prod(map_shape) + vector_size

        return Box(low=-np.inf, high=np.inf, shape=(total_obs_size,), dtype=np.float32)

    def _get_obs(self, agent):
        """
        Constructs the observation vector for the current agent.
        """
        is_red_agent = agent == "player_r"
        map_h, map_w = self.map_size[1], self.map_size[0]

        # --- Map Representation (Multi-channel) ---
        obs_map = np.zeros((self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 7), dtype=np.float32)
        map_view = obs_map[:map_h, :map_w, :]

        # ... (rest of the map population logic is the same) ...
        # Channel 0: Terrain
        my_territory_char = 'R' if is_red_agent else 'B'
        opp_territory_char = 'B' if is_red_agent else 'R'
        for r_idx, row in enumerate(self.game.game_state.floor_tiles):
            for c_idx, tile in enumerate(row):
                if tile == 'P': map_view[r_idx, c_idx, 0] = 1
                elif tile == my_territory_char: map_view[r_idx, c_idx, 0] = 2
                elif tile == opp_territory_char: map_view[r_idx, c_idx, 0] = 3

        # Channels 1-6: Entities
        tower_type_map = {"crossbow": 1, "cannon": 2, "minigun": 3, "house": 4}
        for t in self.game.game_state.towers:
            my_team = (is_red_agent and t.team == 'r') or (not is_red_agent and t.team == 'b')
            map_view[t.y, t.x, 1] = 1
            map_view[t.y, t.x, 2] = t.health
            map_view[t.y, t.x, 3] = 1 if my_team else -1
            map_view[t.y, t.x, 4] = tower_type_map.get(t.name.lower(), 0)
            tower_cooldown_map = {
                "HOUSE": Constants.HOUSE_MAX_COOLDOWN,
                "CANNON": Constants.CANNON_MAX_COOLDOWN,
                "MINIGUN": Constants.MINIGUN_MAX_COOLDOWN,
                "CROSSBOW": Constants.CROSSBOW_MAX_COOLDOWN,
            }
            max_cd = tower_cooldown_map.get(t.name.upper(), 1)
            map_view[t.y, t.x, 5] = t.current_cooldown / max_cd if max_cd > 0 else 0

        merc_state_map = {"walking": 1, "attacking": 2}
        for m in self.game.game_state.mercs:
            my_team = (is_red_agent and m.team == 'r') or (not is_red_agent and m.team == 'b')
            y, x = int(m.y), int(m.x)
            map_view[y, x, 1] = 2
            map_view[y, x, 2] = m.health / Constants.MERCENARY_INITIAL_HEALTH if Constants.MERCENARY_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 1 if my_team else -1
            map_view[y, x, 6] = merc_state_map.get(m.state, 0)

        demon_state_map = {"walking": 1, "attacking": 2}
        for d in self.game.game_state.demons:
            y, x = int(d.y), int(d.x)
            map_view[y, x, 1] = 3
            map_view[y, x, 2] = d.health / Constants.DEMON_INITIAL_HEALTH if Constants.DEMON_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 0
            map_view[y, x, 6] = demon_state_map.get(d.state, 0)

        base_r = self.game.game_state.player_base_r
        base_b = self.game.game_state.player_base_b
        my_base = base_r if is_red_agent else base_b
        opp_base = base_b if is_red_agent else base_r
        map_view[my_base.y, my_base.x, 1] = 4
        map_view[my_base.y, my_base.x, 2] = my_base.health / Constants.PLAYER_BASE_INITIAL_health if Constants.PLAYER_BASE_INITIAL_health > 0 else 0
        map_view[my_base.y, my_base.x, 3] = 1
        map_view[opp_base.y, opp_base.x, 1] = 4
        map_view[opp_base.y, opp_base.x, 2] = opp_base.health / Constants.PLAYER_BASE_INITIAL_health if Constants.PLAYER_BASE_INITIAL_health > 0 else 0
        map_view[opp_base.y, opp_base.x, 3] = -1

        # --- Vector Features ---
        my_money = self.game.game_state.money_r if is_red_agent else self.game.game_state.money_b
        my_base_health = self.game.game_state.player_base_r.health if is_red_agent else self.game.game_state.player_base_b.health
        opp_money = self.game.game_state.money_b if is_red_agent else self.game.game_state.money_r
        opp_base_health = self.game.game_state.player_base_b.health if is_red_agent else self.game.game_state.player_base_r.health
        turns_remaining = self.game.game_state.turns_remaining

        vector_features = np.array([
            my_money, my_base_health, opp_money, opp_base_health, turns_remaining
        ], dtype=np.float32)

        # Normalize vector features
        vector_features[0] /= 1000
        vector_features[1] /= Constants.PLAYER_BASE_INITIAL_health if Constants.PLAYER_BASE_INITIAL_health > 0 else 1
        vector_features[2] /= 1000
        vector_features[3] /= Constants.PLAYER_BASE_INITIAL_health if Constants.PLAYER_BASE_INITIAL_health > 0 else 1
        vector_features[4] /= Constants.MAX_TURNS if Constants.MAX_TURNS > 0 else 1
        
        # --- Flatten and Concatenate ---
        flat_map = obs_map.flatten()
        return np.concatenate([flat_map, vector_features])

    def observe(self, agent):
        return self._get_obs(agent)


    def reset(self, seed=None, options=None):
        # Reset the game
        self.game = Game(self.map_path)

        # Reset PettingZoo state
        self.agents = self.possible_agents[:]
        self._agent_selector.reinit(self.agents)
        self.agent_selection = self._agent_selector.next()

        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}
        
        self.action_r = None
        self.action_b = None

        # Get initial observation
        observation = self._get_obs(self.agent_selection)
        info = self.infos[self.agent_selection]
        
        return observation, info

    def step(self, action):
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            self._was_dead_step(action)
            return

        agent = self.agent_selection
        
        # --- Convert action from MultiDiscrete space to AIAction object ---
        action_type_map = {0: "nothing", 1: "build", 2: "destroy"}
        tower_type_map = {0: "crossbow", 1: "cannon", 2: "minigun", 3: "house"}
        merc_dir_map = {0: "", 1: "N", 2: "S", 3: "E", 4: "W"}

        act_type, x, y, tower_type, merc_dir = action
        
        # --- Validate Action and Clamp Coordinates ---
        map_w, map_h = self.map_size
        
        # Store original x, y from the agent's action before clamping
        original_x, original_y = action[1], action[2] 

        # Clamp x and y to be within the actual map boundaries
        x = np.clip(original_x, 0, map_w - 1)
        y = np.clip(original_y, 0, map_h - 1)

        # If the original action was out of bounds, penalize and convert to "nothing"
        if original_x >= map_w or original_y >= map_h:
            self.rewards[agent] -= 0.1  # Small penalty
            act_type = 0 # Set action to "nothing"

        ai_action = AIAction(
            action=action_type_map[act_type],
            x=x, # Use clamped x
            y=y, # Use clamped y
            tower_type=tower_type_map[tower_type],
            merc_direction=merc_dir_map[merc_dir]
        )

        # --- Store action and wait for other agent ---
        if agent == "player_r":
            self.action_r = ai_action
        else:
            self.action_b = ai_action

        # --- Cycle agent selection ---
        self.agent_selection = self._agent_selector.next()

        # --- If both agents have acted, run the game turn ---
        if self.action_r is not None and self.action_b is not None:
            # Get old state for reward calculation
            old_health_r = self.game.game_state.player_base_r.health
            old_health_b = self.game.game_state.player_base_b.health
            old_merc_count_r = len([m for m in self.game.game_state.mercs if m.team == 'r'])
            old_merc_count_b = len([m for m in self.game.game_state.mercs if m.team == 'b'])
            old_money_r = self.game.game_state.money_r
            old_money_b = self.game.game_state.money_b

            # Run the game turn
            self.game.run_turn(self.action_r, self.action_b)

            # Reset stored actions
            self.action_r = None
            self.action_b = None

            # --- Calculate Rewards ---
            health_r = self.game.game_state.player_base_r.health
            health_b = self.game.game_state.player_base_b.health
            merc_count_r = len([m for m in self.game.game_state.mercs if m.team == 'r'])
            merc_count_b = len([m for m in self.game.game_state.mercs if m.team == 'b'])
            money_r = self.game.game_state.money_r
            money_b = self.game.game_state.money_b

            # --- Reward Components ---

            # 1. Health delta (damage dealt vs. taken)
            health_delta_r = (old_health_b - health_b) - (old_health_r - health_r)
            health_delta_b = (old_health_r - health_r) - (old_health_b - health_b)

            # 2. Mercenary delta (enemies destroyed vs. friendlies lost)
            # This is tricky because new mercs are spawned. A simple count difference is not enough.
            # Let's count destroyed mercs explicitly if possible. For now, this is an approximation.
            destroyed_b = old_merc_count_b - merc_count_b
            lost_r = old_merc_count_r - merc_count_r
            merc_delta_r = destroyed_b - lost_r

            destroyed_r = old_merc_count_r - merc_count_r
            lost_b = old_merc_count_b - merc_count_b
            merc_delta_b = destroyed_r - lost_b

            # 3. Economic delta (income vs. spending)
            # We need to know the cost of the action to calculate true income.
            # Let's approximate with money change.
            income_r = money_r - old_money_r
            income_b = money_b - old_money_b
            
            # Add cost for spawning mercs
            if self.action_r and self.action_r.action == "spawn":
                income_r -= Constants.MERC_COST
            if self.action_b and self.action_b.action == "spawn":
                income_b -= Constants.MERC_COST


            # 4. Time penalty (encourages faster wins)
            time_penalty = -0.01

            # --- Total Reward ---
            # Assign weights to each component
            w_health = 1.0
            w_merc = 0.2
            w_econ = 0.05

            reward_r = (w_health * health_delta_r) + \
                       (w_merc * merc_delta_r) + \
                       (w_econ * income_r) + \
                       time_penalty
            
            reward_b = (w_health * health_delta_b) + \
                       (w_merc * merc_delta_b) + \
                       (w_econ * income_b) + \
                       time_penalty
            
            self.rewards["player_r"] += reward_r
            self.rewards["player_b"] += reward_b

            # --- Check for Termination or Truncation ---
            if self.game.game_state.is_game_over():
                if self.game.game_state.victory == 'r':
                    self.rewards["player_r"] += 100
                    self.rewards["player_b"] -= 100
                elif self.game.game_state.victory == 'b':
                    self.rewards["player_b"] += 100
                    self.rewards["player_r"] -= 100
                
                self.terminations = {a: True for a in self.agents}

            # Update cumulative rewards for all agents after the turn is fully processed
            for a in self.agents:
                self._cumulative_rewards[a] = self.rewards[a]

        # Set info and handle dead agents
        if self.render_mode == "human":
            self.render()

    def render(self):
        # The game has a Godot-based visualizer, which we can't run from here.
        # For now, this will be a no-op.
        pass

    def close(self):
        pass

if __name__ == '__main__':
    # Test the environment
    from pettingzoo.test import api_test

    map_file = str(Path(__file__).resolve().parent.parent / 'maps' / 'test_map.json')
    env = env(map_path=map_file)
    
    print("Running PettingZoo API test...")
    api_test(env, num_cycles=1000, verbose_progress=True)
    print("API test passed!")


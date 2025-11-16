# This script defines the MegaMiner environment for reinforcement learning using the PettingZoo API.
# It acts as a wrapper around the main game logic, allowing RL agents to interact with the game.
# The environment is designed to be used with libraries like Stable Baselines3 for training RL agents.

import gymnasium
import numpy as np
from gymnasium.spaces import Box, Dict, Discrete
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector, wrappers
import sys
from pathlib import Path
import math

# Add the backend directory to the Python path to import game components.
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from Game import Game
from AIAction import AIAction
import Constants

def env(map_path):
    """
    The env function wraps the raw environment in helpful wrappers provided by PettingZoo.
    These wrappers can enforce constraints and perform standard transformations, which is good practice.
    """
    internal_render_mode = "human"
    env = raw_env(render_mode=internal_render_mode, map_path=map_path)
    # This wrapper asserts that actions are within the defined action space.
    # It's useful for debugging during development to catch invalid actions.
    env = wrappers.AssertOutOfBoundsWrapper(env)
    return env

class raw_env(AECEnv):
    """
    The raw environment for MegaMiner, implementing the PettingZoo AECEnv (Agent-Environment-Cycle) API.
    This class handles the core logic of the environment, including:
    - State Management: Tracking the positions of all entities, player health, money, etc.
    - Action Handling: Receiving actions from agents and applying them to the game state.
    - Observation Generation: Converting the game state into a format that RL agents can understand.
    - Reward Calculation: Providing a reward signal to the agents based on their performance.
    """
    metadata = {
        "render_modes": ["human"],  # "human" mode is a placeholder; visualization is handled by a separate Godot project.
        "name": "MegaMiner_v0",
        "is_parallelizable": True,  # The environment can be run in parallel for faster training.
    }

    # Define maximum map dimensions for padding the observation space.
    # This ensures a consistent observation shape regardless of the actual map size, which is required by most RL libraries.
    MAX_MAP_WIDTH = 50
    MAX_MAP_HEIGHT = 50

    def __init__(self, map_path, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        
        # Load the game map and initialize the game state from the backend.
        self.map_path = map_path
        self.game = Game(self.map_path)
        self.map_size = (len(self.game.game_state.floor_tiles[0]), len(self.game.game_state.floor_tiles))

        # --- PettingZoo Setup ---
        # Define the agents that exist in the environment.
        self.agents = ["player_r", "player_b"]
        self.possible_agents = self.agents[:]
        # The agent_selector is a utility that cycles through agents in a round-robin fashion.
        self._agent_selector = agent_selector(self.agents)
        
        # Define the action and observation spaces for the agents. These must be consistent for all agents.
        self._action_space_dict = self._create_action_space()
        self._observation_space_dict = self._create_observation_space()

        # --- Game State Tracking ---
        # These dictionaries store the current state for each agent.
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents} # True if an agent has reached a terminal state (e.g., won/lost).
        self.truncations = {agent: False for agent in self.agents}   # True if the episode is ended for other reasons (e.g., time limit).
        self.infos = {agent: {} for agent in self.agents}            # Auxiliary diagnostic information.

        # In this simultaneous-move game, we need to store the action of the first agent
        # while we wait for the action of the second agent.
        self.action_r = None
        self.action_b = None
        
        # --- Reward System State Tracking ---
        # Track metrics needed for the structured reward system
        self.tower_count_r = 0
        self.tower_count_b = 0
        self.tower_count_r_prev = 0
        self.tower_count_b_prev = 0
        self.enemies_killed_r = 0  # Enemies killed by red player's towers
        self.enemies_killed_b = 0  # Enemies killed by blue player's towers
        self.last_turn = 0
        self.mercenary_count_r_prev = 0
        self.mercenary_count_b_prev = 0

    def observation_space(self, agent):
        """Returns the observation space for a given agent."""
        return self._observation_space_dict

    def action_space(self, agent):
        """Returns the action space for a given agent."""
        return self._action_space_dict

    def _create_action_space(self):
        """
        Defines the action space for an agent.
        We use a MultiDiscrete space, which is a flat vector of discrete choices.
        This is a common way to represent a complex action space for an RL agent.
        The vector is structured as: [action_type, x, y, tower_type, merc_direction]
        """
        return gymnasium.spaces.MultiDiscrete([
            3,  # action_type: 0=nothing, 1=build, 2=destroy
            self.MAX_MAP_WIDTH,  # x-coordinate for the action (0 to MAX_MAP_WIDTH-1)
            self.MAX_MAP_HEIGHT, # y-coordinate for the action (0 to MAX_MAP_HEIGHT-1)
            4,  # tower_type: 0=crossbow, 1=cannon, 2=minigun, 3=house
            5   # merc_direction: 0="", 1=N, 2=S, 3=E, 4=W (used for spawning mercenaries)
        ])

    def _create_observation_space(self):
        """
        Defines the observation space for an agent.
        The observation is a flattened vector combining a multi-channel map representation
        and a vector of game state features. This is suitable for an MLP (Multi-Layer Perceptron) policy.
        A CNN (Convolutional Neural Network) could also be used if the map representation is kept as a 3D tensor.
        """
        # The map is represented as a 3D tensor (Height, Width, Channels).
        map_shape = (self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 9)
        # The vector part contains additional global game state information.
        vector_size = 10
        
        # The total observation size is the flattened map plus the vector features.
        total_obs_size = np.prod(map_shape) + vector_size

        return Box(low=-np.inf, high=np.inf, shape=(total_obs_size,), dtype=np.float32)

    def _get_obs(self, agent):
        """
        Constructs the observation vector for the current agent.
        This function gathers all relevant game state information and packs it into the format
        defined by the observation space. It is crucial that this function is deterministic and
        accurately reflects the game state.
        """
        is_red_agent = agent == "player_r"
        map_h, map_w = self.map_size[1], self.map_size[0]

        # --- Map Representation (Multi-channel) ---
        # Multi-channel map to represent spatial information. Each channel represents a different aspect of the game state.
        obs_map = np.zeros((self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 9), dtype=np.float32)
        map_view = obs_map[:map_h, :map_w, :]  # view for easier indexing into non-padded area

        # --- Channel 0: Terrain Type ---
        # Encodes the type of each tile: 1=Path, 2=My Territory, 3=Opponent's Territory
        my_territory_char = 'R' if is_red_agent else 'B'
        opp_territory_char = 'B' if is_red_agent else 'R'
        for r_idx, row in enumerate(self.game.game_state.floor_tiles):
            for c_idx, tile in enumerate(row):
                if tile == 'P': map_view[r_idx, c_idx, 0] = 1
                elif tile == my_territory_char: map_view[r_idx, c_idx, 0] = 2
                elif tile == opp_territory_char: map_view[r_idx, c_idx, 0] = 3

        # --- Entity Channels ---
        # Channel 1: Entity Type (1: Tower, 2: Merc, 3: Demon, 4: Base)
        # Channel 2: Health (normalized for mercs, demons, bases)
        # Channel 3: Team Affiliation (1: Mine, -1: Opponent's, 0: Neutral)
        # Channel 4: Tower Type (1-4 for different tower types)
        # Channel 5: Tower Cooldown (normalized)
        # Channel 6: Unit State (1: walking, 2: attacking)
        # Channel 7: Heat Map of Users Damage-to-Range
        # Channel 8: Heat Map of Opponents Damage-to-Range
        
        tower_type_map = {"crossbow": 1, "cannon": 2, "minigun": 3, "house": 4}
        tower_cooldown_map = {
            "HOUSE": Constants.HOUSE_MAX_COOLDOWN,
            "CANNON": Constants.CANNON_MAX_COOLDOWN,
            "MINIGUN": Constants.MINIGUN_MAX_COOLDOWN,
            "CROSSBOW": Constants.CROSSBOW_MAX_COOLDOWN,
        }

        # --- Initialize Damage-Per-Tile Heatmaps ---
        my_dpt_map = np.zeros((map_h, map_w), dtype=np.float32)
        opp_dpt_map = np.zeros((map_h, map_w), dtype=np.float32)

        # Tower stats maps (damage and range) excluding House/Church
        tower_damage_map = {
            "CANNON": Constants.CANNON_DAMAGE,
            "MINIGUN": Constants.MINIGUN_DAMAGE,
            "CROSSBOW": Constants.CROSSBOW_DAMAGE,
        }

        tower_range_map = {
            "CANNON": Constants.CANNON_RANGE,
            "MINIGUN": Constants.MINIGUN_RANGE,
            "CROSSBOW": Constants.CROSSBOW_RANGE,
        }

        for t in self.game.game_state.towers:
            my_team = (is_red_agent and t.team == 'r') or (not is_red_agent and t.team == 'b')
            map_view[t.y, t.x, 1] = 1
            map_view[t.y, t.x, 2] = t.health
            map_view[t.y, t.x, 3] = 1 if my_team else -1
            map_view[t.y, t.x, 4] = tower_type_map.get(t.name.lower(), 0)
            max_cd = tower_cooldown_map.get(t.name.upper(), 1)
            map_view[t.y, t.x, 5] = t.current_cooldown / max_cd if max_cd > 0 else 0

            # --- Apply Damage-Per-Tile heatmap for offensive towers (only on path tiles) ---
            t_type_upper = t.name.upper()
            if t_type_upper in tower_damage_map:
                damage = tower_damage_map[t_type_upper]
                rng = tower_range_map[t_type_upper]
                damage_per_turn = damage / max_cd if max_cd > 0 else damage

                for dy in range(-rng, rng + 1):
                    for dx in range(-rng, rng + 1):
                        ny, nx = t.y + dy, t.x + dx
                        if 0 <= ny < map_h and 0 <= nx < map_w:
                            # Only add damage if the tile is a path (channel 0 == 1)
                            if map_view[ny, nx, 0] == 1:
                                if my_team:
                                    my_dpt_map[ny, nx] += damage_per_turn
                                else:
                                    opp_dpt_map[ny, nx] += damage_per_turn

        # my_dpt_flat = my_dpt_map.flatten()
        # opp_dpt_flat = opp_dpt_map.flatten()

        map_view[:, :, 7] = my_dpt_map
        map_view[:, :, 8] = opp_dpt_map

        # --- Mercenaries ---
        merc_state_map = {"walking": 1, "attacking": 2}
        for m in self.game.game_state.mercs:
            my_team = (is_red_agent and m.team == 'r') or (not is_red_agent and m.team == 'b')
            y, x = int(m.y), int(m.x)
            map_view[y, x, 1] = 2
            map_view[y, x, 2] = m.health / Constants.MERCENARY_INITIAL_HEALTH if Constants.MERCENARY_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 1 if my_team else -1
            map_view[y, x, 6] = merc_state_map.get(m.state, 0)

        # --- Demons ---
        demon_state_map = {"walking": 1, "attacking": 2}
        for d in self.game.game_state.demons:
            y, x = int(d.y), int(d.x)
            map_view[y, x, 1] = 3
            map_view[y, x, 2] = d.health / Constants.DEMON_INITIAL_HEALTH if Constants.DEMON_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 0
            map_view[y, x, 6] = demon_state_map.get(d.state, 0)

        # --- Bases ---
        base_r = self.game.game_state.player_base_r
        base_b = self.game.game_state.player_base_b
        my_base = base_r if is_red_agent else base_b
        opp_base = base_b if is_red_agent else base_r
        map_view[my_base.y, my_base.x, 1] = 4
        map_view[my_base.y, my_base.x, 2] = my_base.health / Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 0
        map_view[my_base.y, my_base.x, 3] = 1
        map_view[opp_base.y, opp_base.x, 1] = 4
        map_view[opp_base.y, opp_base.x, 2] = opp_base.health / Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 0
        map_view[opp_base.y, opp_base.x, 3] = -1

        # --- Vector Features (Global game state) ---
        my_money = self.game.game_state.money_r if is_red_agent else self.game.game_state.money_b
        my_base_health = my_base.health
        opp_money = self.game.game_state.money_b if is_red_agent else self.game.game_state.money_r
        opp_base_health = opp_base.health
        turns_remaining = self.game.game_state.turns_remaining

        House_Cost = self.game.game_state.house_price_r if is_red_agent else self.game.game_state.house_price_b 
        Crossbow_Cost = self.game.game_state.crossbow_price_r if is_red_agent else self.game.game_state.crossbow_price_b 
        Cannon_Cost = self.game.game_state.cannon_price_r if is_red_agent else self.game.game_state.cannon_price_b 
        Minigun_Cost = self.game.game_state.minigun_price_r if is_red_agent else self.game.game_state.minigun_price_b 
        Church_Cost = self.game.game_state.church_price_r if is_red_agent else self.game.game_state.church_price_b 



        vector_features = np.array([
            my_money, my_base_health, opp_money, opp_base_health, turns_remaining,
            House_Cost, Crossbow_Cost, Cannon_Cost, Minigun_Cost, Church_Cost
        ], dtype=np.float32)

        # Normalize vector features (same as in training environment)
        vector_features[0] /= 1000
        vector_features[1] /= Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 1
        vector_features[2] /= 1000
        vector_features[3] /= Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 1
        vector_features[4] /= Constants.MAX_TURNS if Constants.MAX_TURNS > 0 else 1
        vector_features[5:10] /= 1000  # tower costs

        # --- Flatten and Concatenate ---
        # Flatten the map and concatenate it with vector features to form the full observation
        flat_map = obs_map.flatten()
        return np.concatenate([flat_map, vector_features])

    def observe(self, agent):
        """
        Returns the observation for the specified agent.
        This is the public method called by the agent to get its observation.
        """
        return self._get_obs(agent)




    # def _count_towers(self, team):
    #     """Count the number of towers built by a team."""
    #     count = 0
    #     for tower in self.game.game_state.towers:
    #         if tower.team == team:
    #             count += 1
    #     return count

    # def _calculate_tower_placement_quality(self, team, is_red_agent):
    #     """
    #     Calculate a quality score for tower placement based on damage heatmap.
    #     Higher values in friendly damage heatmap at tower locations indicate better placement.
    #     """
    #     map_h, map_w = self.map_size[1], self.map_size[0]
        
    #     # Build friendly damage heatmap
    #     tower_damage_map = {
    #         "CANNON": Constants.CANNON_DAMAGE,
    #         "MINIGUN": Constants.MINIGUN_DAMAGE,
    #         "CROSSBOW": Constants.CROSSBOW_DAMAGE,
    #     }
    #     tower_range_map = {
    #         "CANNON": Constants.CANNON_RANGE,
    #         "MINIGUN": Constants.MINIGUN_RANGE,
    #         "CROSSBOW": Constants.CROSSBOW_RANGE,
    #     }
    #     tower_cooldown_map = {
    #         "HOUSE": Constants.HOUSE_MAX_COOLDOWN,
    #         "CANNON": Constants.CANNON_MAX_COOLDOWN,
    #         "MINIGUN": Constants.MINIGUN_MAX_COOLDOWN,
    #         "CROSSBOW": Constants.CROSSBOW_MAX_COOLDOWN,
    #     }
        
    #     my_dpt_map = np.zeros((map_h, map_w), dtype=np.float32)
    #     placement_score = 0.0
        
    #     for t in self.game.game_state.towers:
    #         my_team = (is_red_agent and t.team == 'r') or (not is_red_agent and t.team == 'b')
    #         if not my_team:
    #             continue
            
    #         t_type_upper = t.name.upper()
    #         if t_type_upper in tower_damage_map:
    #             damage = tower_damage_map[t_type_upper]
    #             rng = tower_range_map[t_type_upper]
    #             max_cd = tower_cooldown_map.get(t_type_upper, 1)
    #             damage_per_turn = damage / max_cd if max_cd > 0 else damage
                
    #             # Calculate coverage value at this tower's position
    #             for dy in range(-rng, rng + 1):
    #                 for dx in range(-rng, rng + 1):
    #                     ny, nx = t.y + dy, t.x + dx
    #                     if 0 <= ny < map_h and 0 <= nx < map_w:
    #                         my_dpt_map[ny, nx] += damage_per_turn
                
    #             # Tower placement quality = sum of damage coverage in its range
    #             placement_score += np.sum(my_dpt_map[
    #                 max(0, t.y - rng):min(map_h, t.y + rng + 1),
    #                 max(0, t.x - rng):min(map_w, t.x + rng + 1)
    #             ])
        
    #     return placement_score

    # def _count_enemies_killed(self):
    #     """
    #     Detect enemies killed by counting changes in enemy counts.
    #     Returns (red_kills, blue_kills) since last check.
    #     """
    #     merc_count_r = sum(1 for m in self.game.game_state.mercs if m.team == 'b')
    #     merc_count_b = sum(1 for m in self.game.game_state.mercs if m.team == 'r')
    #     demon_count = len(self.game.game_state.demons)
        
    #     # Estimate kills from mercenary count changes
    #     # Red player kills blue mercenaries, blue player kills red mercenaries
    #     prev_mercs = self.mercenary_count_r_prev + self.mercenary_count_b_prev
    #     curr_mercs = merc_count_r + merc_count_b
        
    #     self.mercenary_count_r_prev = merc_count_r
    #     self.mercenary_count_b_prev = merc_count_b
        
    #     return 0, 0  # Placeholder - would need more detailed tracking

    # def _check_invalid_action(self, action, agent, is_red_agent):
    #     """
    #     Check if an action is invalid and return penalty if so.
    #     Invalid actions include:
    #     - Building on occupied tiles
    #     - Building on enemy/restricted tiles (CRITICALLY PENALIZED)
    #     - Building without sufficient money (HEAVILY PENALIZED)
    #     - Out of bounds actions (HEAVILY PENALIZED)
    #     """
    #     act_type, x, y, tower_type, merc_dir = action
    #     action_type_map = {0: "nothing", 1: "build", 2: "destroy"}
    #     tower_type_map = {0: "crossbow", 1: "cannon", 2: "minigun", 3: "house", 4: "church"}
        
    #     penalty = 0.0
    #     map_w, map_h = self.map_size
        
    #     # Check if action is out of bounds (HEAVY PENALTY)
    #     if x >= map_w or y >= map_h or x < 0 or y < 0:
    #         penalty = -1.0  # HEAVILY PENALIZE out of bounds
    #         return penalty
        
    #     # For build actions, check validity
    #     if act_type == 1:  # build
    #         # ========== CRITICAL CHECK: BUILDING IN OWN TERRITORY ==========
    #         # This is the most important check - agent MUST learn to only build in own territory
    #         my_territory_char = 'R' if is_red_agent else 'B'
    #         actual_tile = self.game.game_state.floor_tiles[y][x]
            
    #         # CRITICAL PENALTY: Building outside own territory (enemy/neutral)
    #         if actual_tile != my_territory_char:
    #             penalty = -5.0  # EXTREMELY HEAVY PENALTY for building outside territory
    #             return penalty
            
    #         current_money = self.game.game_state.money_r if is_red_agent else self.game.game_state.money_b
    #         tower_type_str = tower_type_map.get(tower_type, "crossbow").lower()
            
    #         # Get tower price
    #         if is_red_agent:
    #             tower_prices = {
    #                 "crossbow": self.game.game_state.crossbow_price_r,
    #                 "cannon": self.game.game_state.cannon_price_r,
    #                 "minigun": self.game.game_state.minigun_price_r,
    #                 "house": self.game.game_state.house_price_r,
    #                 "church": self.game.game_state.church_price_r,
    #             }
    #         else:
    #             tower_prices = {
    #                 "crossbow": self.game.game_state.crossbow_price_b,
    #                 "cannon": self.game.game_state.cannon_price_b,
    #                 "minigun": self.game.game_state.minigun_price_b,
    #                 "house": self.game.game_state.house_price_b,
    #                 "church": self.game.game_state.church_price_b,
    #             }
            
    #         tower_cost = tower_prices.get(tower_type_str, 100)
            
    #         # HEAVY PENALTY: Trying to build without sufficient money
    #         if current_money < tower_cost:
    #             penalty = -2.0  # VERY HEAVY PENALTY for attempting purchase without money
            
    #         # HEAVY PENALTY: Building on occupied tiles
    #         for entity in self.game.game_state.towers + self.game.game_state.mercs + self.game.game_state.demons:
    #             if entity.x == x and entity.y == y:
    #                 penalty = -1.5  # HEAVY PENALTY for occupied tile
    #                 break
        
    #     return penalty

    # def _check_invalid_mercenary_purchase(self, action, is_red_agent):
    #     """
    #     Check if agent is trying to buy a mercenary without money.
    #     Returns heavy penalty if attempting to buy without funds or buying too many.
    #     Also penalizes mercenary spam.
    #     """
    #     act_type, x, y, tower_type, merc_dir = action
        
    #     # Check if action includes mercenary purchase (merc_dir is not empty)
    #     if merc_dir != 0:  # 0 = "", 1+ = valid direction
    #         current_money = self.game.game_state.money_r if is_red_agent else self.game.game_state.money_b
    #         mercenary_cost = Constants.MERCENARY_PRICE  # $10
            
    #         # Count existing mercenaries for this player
    #         merc_count = sum(1 for m in self.game.game_state.mercs if m.team == ('r' if is_red_agent else 'b'))
            
    #         # EXTREMELY HEAVY PENALTY: Trying to buy mercenary without sufficient money
    #         if current_money < mercenary_cost:
    #             return -3.0  # EXTREMELY HEAVY PENALTY for mercenary without funds
            
    #         # HEAVY PENALTY: Spamming mercenaries (more than 8 at once)
    #         # Encourages strategic use, not spam
    #         if merc_count >= 8:
    #             return -1.5  # Penalty for having too many mercenaries
        
    #     return 0.0

    # def _is_early_game(self):
    #     """Check if we're in the early game (first 30 turns)."""
    #     return Constants.MAX_TURNS - self.game.game_state.turns_remaining < 30

    def reset(self, seed=None, options=None):
        """
        Resets the environment to its initial state for a new episode and returns the initial observation.
        """
        # Reset the underlying game engine to a fresh state.
        self.game = Game(self.map_path)

        # Reset the PettingZoo-specific state for the new episode.
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
        
        # Reset reward system state tracking
        self.tower_count_r = 0
        self.tower_count_b = 0
        self.tower_count_r_prev = 0
        self.tower_count_b_prev = 0
        self.enemies_killed_r = 0
        self.enemies_killed_b = 0
        self.last_turn = 0
        self.mercenary_count_r_prev = 0
        self.mercenary_count_b_prev = 0

        # Get the initial observation for the first agent to act.
        observation = self._get_obs(self.agent_selection)
        info = self.infos[self.agent_selection]
        
        return observation, info

    def step(self, action):
        """
        Takes a step in the environment for the current agent.
        This involves storing the agent's action, and if all agents have acted,
        running a game turn, calculating rewards, and checking for termination.
        """
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            # If the agent is done, it shouldn't be able to act. Handle this gracefully.
            self._was_dead_step(action)
            return

        agent = self.agent_selection
        
        # --- Decode and Validate Action ---
        action_type_map = {0: "nothing", 1: "build", 2: "destroy"}
        tower_type_map = {0: "crossbow", 1: "cannon", 2: "minigun", 3: "house", 4: "church"}
        merc_dir_map = {0: "", 1: "N", 2: "S", 3: "E", 4: "W"}

        act_type, x, y, tower_type, merc_dir = action
        
        map_w, map_h = self.map_size
        original_x, original_y = action[1], action[2] 

        # Clamp coordinates to be within the map boundaries.
        x = np.clip(original_x, 0, map_w - 1)
        y = np.clip(original_y, 0, map_h - 1)
        is_out_of_bounds = original_x >= map_w or original_y >= map_h

        # --- 1. ACTION VALIDITY CHECK (HEAVY PENALTIES) ---
        # Penalize invalid actions heavily to encourage proper behavior
        #invalid_penalty = self._check_invalid_action(action, agent, is_red_agent)
        #mercenary_purchase_penalty = self._check_invalid_mercenary_purchase(action, is_red_agent)
        
        # If the agent chose an action outside the map, penalize it HEAVILY and force a "nothing" action.
        if original_x >= map_w or original_y >= map_h:
            act_type = 0  # Force "nothing" action.
            # Already penalized by invalid_penalty

        ai_action = AIAction(
            action=action_type_map[act_type], x=x, y=y,
            tower_type=tower_type_map[tower_type], merc_direction=merc_dir_map[merc_dir]
        )

        # --- Store action and wait for the other agent ---
        if agent == "player_r":
            self.action_r = ai_action
        else:
            self.action_b = ai_action

        # --- Cycle agent selection for the next turn ---
        self.agent_selection = self._agent_selector.next()

        # --- If both agents have acted, run the game turn ---
        if self.action_r is not None and self.action_b is not None:
            old_health_r = self.game.game_state.player_base_r.health
            old_health_b = self.game.game_state.player_base_b.health
            old_money_r = self.game.game_state.money_r
            old_money_b = self.game.game_state.money_b
            old_house_cost_r = self.game.game_state.house_price_r
            old_house_cost_b = self.game.game_state.house_price_b 
            old_crossbow_cost_r = self.game.game_state.crossbow_price_r
            old_crossbow_cost_b = self.game.game_state.crossbow_price_b 
            old_cannon_cost_r = self.game.game_state.cannon_price_r
            old_cannon_cost_b = self.game.game_state.cannon_price_b 
            old_minigun_cost_r = self.game.game_state.minigun_price_r
            old_minigun_cost_b = self.game.game_state.minigun_price_b 
            old_church_cost_r = self.game.game_state.church_price_r
            old_church_cost_b = self.game.game_state.church_price_b 

            old_action_r = self.action_r
            old_action_b = self.action_b
            # Run the game turn with the actions from both agents.
            self.game.run_turn(self.action_r, self.action_b)

            # Reset stored actions for the next turn.
            self.action_r = None
            self.action_b = None

            # --- Calculate Rewards ---
            # Reward shaping is crucial for training RL agents effectively.
            # We use a sparse reward for winning/losing and a dense reward for in-game events.
            health_r = self.game.game_state.player_base_r.health
            health_b = self.game.game_state.player_base_b.health
            money_r = self.game.game_state.money_r
            money_b = self.game.game_state.money_b
            house_cost_r = self.game.game_state.house_price_r
            house_cost_b = self.game.game_state.house_price_b 
            crossbow_cost_r = self.game.game_state.crossbow_price_r
            crossbow_cost_b = self.game.game_state.crossbow_price_b 
            cannon_cost_r = self.game.game_state.cannon_price_r
            cannon_cost_b = self.game.game_state.cannon_price_b 
            minigun_cost_r = self.game.game_state.minigun_price_r
            minigun_cost_b = self.game.game_state.minigun_price_b 
            church_cost_r = self.game.game_state.church_price_r
            church_cost_b = self.game.game_state.church_price_b 

            house_built_r = 0 if(old_house_cost_r == house_cost_r) else 1
            house_built_b = 0 if(old_house_cost_b == house_cost_b) else 1
            crossbow_built_r = 0 if(old_crossbow_cost_r == crossbow_cost_r) else 1
            crossbow_built_b = 0 if(old_crossbow_cost_b == crossbow_cost_b) else 1
            cannon_built_r = 0 if(old_cannon_cost_r == cannon_cost_r) else 1
            cannon_built_b = 0 if(old_cannon_cost_b == cannon_cost_b) else 1
            minigun_built_r = 0 if(old_minigun_cost_r == minigun_cost_r) else 1
            minigun_built_b = 0 if(old_minigun_cost_b == minigun_cost_b) else 1
            church_built_r = 0 if(old_church_cost_r == church_cost_r) else 1
            church_built_b = 0 if(old_church_cost_b == church_cost_b) else 1
            

            # === REWARD RED PLAYER ===
            reward_r = 0.0
            
            #Losing Health Penalty
            health_r_delta = health_r - old_health_r
            if health_r_delta < 0:
                reward_r -= 0.13 * abs(health_r_delta)

            #Enemy losing Health Reward
            health_b_delta = health_b - old_health_b
            if health_b_delta > 0:
                reward_r += 0.06 * abs(health_b_delta)

            #Money less than 10 Penalty
            if money_r <= 10:
                reward_r -= 0.03

            if house_built_r:
                reward_r += 0.08

            if old_action_r.action == "nothing":
                if old_action_r.merc_direction != "" and old_money_r - 10 <= 0:
                    reward_r -=0.04
            elif old_action_r.action == "build":
                tower_chosen = old_action_r.tower_type
                tower_cost = 0
                if tower_chosen == "cannon":
                    tower_cost = old_cannon_cost_r
                elif tower_chosen == "crossbow":
                    tower_cost = old_crossbow_cost_r
                elif tower_chosen == "minigun":
                    tower_cost = old_minigun_cost_r
                elif tower_chosen == "house":
                    tower_cost = old_house_cost_r
                elif tower_chosen == "church":
                    tower_cost = old_church_cost_r
                if old_money_r - tower_cost < 0:
                    reward_r -=0.04
            elif  old_action_r.action == "destroy":
                reward_r -= 0.04



            #Spending more than Current Penalty
            if(old_action_r.action == "build"):
                reward_r+=0.07
            
            #Check if the tile is valid for building (only if attempting to build)
            is_valid_build = False
            if old_action_r.action == "build":  # "build" action
                my_territory_char = 'R'
                tile_char = self.game.game_state.floor_tiles[old_action_r.y][old_action_r.x] if not is_out_of_bounds else None
                has_entity = self.game.game_state.entity_grid[old_action_r.y][old_action_r.x] is not None if not is_out_of_bounds else True
                is_valid_build = (tile_char == my_territory_char and not has_entity)

             #Apply penalties for invalid actions
            if is_out_of_bounds:
                reward_r-= 0.04  # Penalty for choosing out-of-bounds tile
            elif  old_action_r.action == "build" and not is_valid_build:
                reward_r -= 0.04  # Stronger penalty for invalid build location
            elif  old_action_r.action == "build" and is_valid_build:
                reward_r += 0.04


            #reward_r -= 0.01

            # === REWARD BLUE PLAYER (symmetrical) ===
            reward_b = 0.0
            
            #Losing Health Penalty
            health_b_delta = health_b - old_health_b
            if health_b_delta < 0:
                reward_b -= 0.13 * abs(health_b_delta)

            #Enemy losing Health Reward
            health_r_delta = health_r - old_health_r
            if health_r_delta > 0:
                reward_b += 0.06 * abs(health_r_delta)

            #Money less than 10 Penalty
            if money_b <= 10:
                reward_b -= 0.03

            if house_built_b:
                reward_r += 0.08

            if old_action_b.action == "nothing":
                if old_action_b.merc_direction != "" and old_money_b - 10 <= 0:
                    reward_b -=0.04
            elif old_action_b.action == "build":
                tower_chosen = old_action_b.tower_type
                tower_cost = 0
                if tower_chosen == "cannon":
                    tower_cost = old_cannon_cost_b
                elif tower_chosen == "crossbow":
                    tower_cost = old_crossbow_cost_b
                elif tower_chosen == "minigun":
                    tower_cost = old_minigun_cost_b
                elif tower_chosen == "house":
                    tower_cost = old_house_cost_b
                elif tower_chosen == "church":
                    tower_cost = old_church_cost_b
                if old_money_b - tower_cost < 0:
                    reward_b -=0.04
            elif  old_action_b.action == "destroy":
                reward_b -= 0.04



            #Spending more than Current Penalty
            if(old_action_b.action == "build"):
                reward_b+=0.07
            
            #Check if the tile is valid for building (only if attempting to build)
            is_valid_build = False
            if old_action_b.action == "build":  # "build" action
                my_territory_char = 'B'
                tile_char = self.game.game_state.floor_tiles[old_action_b.y][old_action_b.x] if not is_out_of_bounds else None
                has_entity = self.game.game_state.entity_grid[old_action_b.y][old_action_b.x] is not None if not is_out_of_bounds else True
                is_valid_build = (tile_char == my_territory_char and not has_entity)

             #Apply penalties for invalid actions
            if is_out_of_bounds:
                reward_b-= 0.04  # Penalty for choosing out-of-bounds tile
            elif  old_action_b.action == "build" and not is_valid_build:
                reward_b -= 0.04  # Stronger penalty for invalid build location
            elif  old_action_b.action == "build" and is_valid_build:
                reward_b += 0.04

 
            
            # Update tower count tracking for next turn
            self.tower_count_r_prev = self.tower_count_r
            self.tower_count_b_prev = self.tower_count_b
            
            self.rewards["player_r"] = reward_r
            self.rewards["player_b"] = reward_b

            print("R",self.rewards["player_r"], "B",self.rewards["player_b"])
            # --- Check for Termination (Game Over) ---
            if self.game.game_state.is_game_over():
                # Win/Loss conditions with large sparse rewards
                if self.game.game_state.victory == 'r':
                    self.rewards["player_r"] += 100.0  # Large reward for winning
                    self.rewards["player_b"] -= 100.0  # Large penalty for losing
                elif self.game.game_state.victory == 'b':
                    self.rewards["player_b"] += 100.0
                    self.rewards["player_r"] -= 100.0
                
                self.terminations = {a: True for a in self.agents}

            # Update cumulative rewards for logging and debugging.
            for a in self.agents:
                self._cumulative_rewards[a] += self.rewards[a]

        # Handle rendering if enabled.
        if self.render_mode == "human":
            self.render()

    def render(self):
        """
        The game has a Godot-based visualizer, which is a separate process.
        This function is a no-op as rendering is not handled directly within this environment.
        """
        pass

    def close(self):
        """
        Cleans up any resources used by the environment.
        """
        pass

if __name__ == '__main__':
    # This block is for testing the environment to ensure it conforms to the PettingZoo API.
    from pettingzoo.test import api_test

    map_file = str(Path(__file__).resolve().parent.parent / 'maps' / 'map0.json')
    env = env(map_path=map_file)
    
    print("Running PettingZoo API test...")
    # The API test runs a series of checks to ensure the environment is correctly implemented.
    api_test(env, num_cycles=1000, verbose_progress=True)
    print("API test passed!")

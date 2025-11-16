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

# Add the backend directory to the Python path to import game components.
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from Game import Game
from AIAction import AIAction
import Constants


def get_available_build_spaces(game, team_color: str):
    """
    Return a list of (x, y) coordinates on tiles owned by team_color
    that do not currently have an entity on them.
    """
    result = []
    gs = game.game_state  # GameState object

    for y, row in enumerate(gs.floor_tiles):
        for x, tile_owner in enumerate(row):
            if tile_owner == team_color:
                # entity_grid is a 2D array of entities or None
                if gs.entity_grid[y][x] is None:
                    result.append((x, y))

    return result


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
            5,  # tower_type: 0=crossbow, 1=cannon, 2=minigun, 3=house, 4=church
            5   # merc_direction: 0="", 1=N, 2=S, 3=E, 4=W (used for spawning mercenaries)
        ])

    def _create_observation_space(self):
        """
        Defines the observation space for an agent.
        The observation is a Dict space containing:
        - 'map': A 3D tensor (50x50x9) representing the spatial map with multiple channels
        - 'vector': A 1D vector (10,) containing global game state features
        This is ideal for CNN policies that can process spatial information efficiently.
        """
        # The map is represented as a 3D tensor (Height, Width, Channels).
        map_space = Box(low=-np.inf, high=np.inf, shape=(self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 7), dtype=np.float32)
        
        # The vector part contains additional global game state information.
        vector_space = Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)
        
        # Return a Dict space combining both
        return Dict({
            'map': map_space,
            'vector': vector_space
        })

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
        obs_map = np.zeros((self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 7), dtype=np.float32)
        map_view = obs_map[:map_h, :map_w, :]  # view for easier indexing into non-padded area

        # --- Channel 0: Terrain Type ---
        # Encodes the type of each tile: 1=Path, 2=My Territory, 3=Opponent's Territory
        my_territory_char = 'r' if is_red_agent else 'b'
        opp_territory_char = 'b' if is_red_agent else 'r'
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
            #map_view[t.y, t.x, 7] = t.current_cooldown / max_cd if max_cd > 0 else 0

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

        map_view[:, :, 5] = my_dpt_map
        map_view[:, :, 6] = opp_dpt_map

        # --- Mercenaries ---
        merc_state_map = {"walking": 1, "attacking": 2}
        for m in self.game.game_state.mercs:
            my_team = (is_red_agent and m.team == 'r') or (not is_red_agent and m.team == 'b')
            y, x = int(m.y), int(m.x)
            map_view[y, x, 1] = 2
            map_view[y, x, 2] = m.health / Constants.MERCENARY_INITIAL_HEALTH if Constants.MERCENARY_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 1 if my_team else -1
            #map_view[y, x, 5] = merc_state_map.get(m.state, 0)

        # --- Demons ---
        demon_state_map = {"walking": 1, "attacking": 2}
        for d in self.game.game_state.demons:
            y, x = int(d.y), int(d.x)
            map_view[y, x, 1] = 3
            map_view[y, x, 2] = d.health / Constants.DEMON_INITIAL_HEALTH if Constants.DEMON_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 0
            #map_view[y, x, 5] = demon_state_map.get(d.state, 0)

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
        vector_features[0] /= 100
        vector_features[1] /= Constants.PLAYER_BASE_INITIAL_HEALTH
        vector_features[2] /= 100
        vector_features[3] /= Constants.PLAYER_BASE_INITIAL_HEALTH
        vector_features[4] /= Constants.MAX_TURNS
        vector_features[5:10] /= 100  # tower costs

        # --- Return observation as Dict with 3D map structure ---
        # Keep map as 3D tensor (50x50x9) for CNN policies
        # Include vector features separately
        return {
            'map': obs_map,
            'vector': vector_features
        }

    def observe(self, agent):
        """
        Returns the observation for the specified agent.
        This is the public method called by the agent to get its observation.
        """
        return self._get_obs(agent)

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

        # --- Decode action from MultiDiscrete ---
        action_type_map = {0: "nothing", 1: "build", 2: "destroy"}
        tower_type_map = {0: "crossbow", 1: "cannon", 2: "minigun", 3: "house", 4: "church"}
        merc_dir_map = {0: "", 1: "N", 2: "S", 3: "E", 4: "W"}

        act_type, x, y, tower_type, merc_dir = action

        map_w, map_h = self.map_size
        original_x, original_y = x, y

        # --- Enforce map boundaries ---
        x = np.clip(original_x, 0, map_w - 1)
        y = np.clip(original_y, 0, map_h - 1)

        # # Out-of-bounds: penalize and force "nothing"
        # if original_x >= map_w or original_y >= map_h or original_x < 0 or original_y < 0:
        #     # small but consistent penalty
        #     self.rewards[agent] -= 0.2
        #     act_type = 0
        #     merc_dir = 0


        team_color = 'r' if agent == "player_r" else 'b'


        valid_build_spaces = set(get_available_build_spaces(self.game, team_color))

        # If the chosen (x, y) is not a valid tile for this player, penalize and force "nothing"
        
        if (x, y) not in valid_build_spaces and act_type in (1, 2):  # build/destroy only
            self.rewards[agent] -= 0.1
            act_type = 0          # do nothing
            merc_dir = 0          # no mercs this turn

        # --- Enforce: merc_direction only allowed when doing NOTHING ---
        # If the agent tries to build/destroy AND set a merc direction, we zero it and penalize.
        if act_type != 0 and merc_dir != 0:
            # can't send mercs while building/destroying
            self.rewards[agent] -= 0.1
            merc_dir = 0

        # Convert to AIAction used by the backend Game
        ai_action = AIAction(
            action=action_type_map[act_type],
            x=x,
            y=y,
            tower_type=tower_type_map[tower_type],
            merc_direction=merc_dir_map[merc_dir]
        )

        print(agent,action_type_map[act_type], tower_type_map[tower_type],merc_dir_map[merc_dir])

        # --- Store action and wait for the other agent ---
        if agent == "player_r":
            self.action_r = ai_action
        else:
            self.action_b = ai_action

        # --- Cycle to the next agent ---
        self.agent_selection = self._agent_selector.next()

        # --- If both agents have acted, run a game turn and compute rewards ---
        if self.action_r is not None and self.action_b is not None:
            # Snapshot state BEFORE running the turn
            old_health_r = self.game.game_state.player_base_r.health
            old_health_b = self.game.game_state.player_base_b.health
            old_money_r = self.game.game_state.money_r
            old_money_b = self.game.game_state.money_b

            # Tower prices (we'll use price changes to detect builds)
            old_house_cost_r    = self.game.game_state.house_price_r
            old_house_cost_b    = self.game.game_state.house_price_b
            old_crossbow_cost_r = self.game.game_state.crossbow_price_r
            old_crossbow_cost_b = self.game.game_state.crossbow_price_b
            old_cannon_cost_r   = self.game.game_state.cannon_price_r
            old_cannon_cost_b   = self.game.game_state.cannon_price_b
            old_minigun_cost_r  = self.game.game_state.minigun_price_r
            old_minigun_cost_b  = self.game.game_state.minigun_price_b
            old_church_cost_r   = self.game.game_state.church_price_r
            old_church_cost_b   = self.game.game_state.church_price_b

            # Keep references to the actions *used* this turn
            old_action_r = self.action_r
            old_action_b = self.action_b

            # Run the game logic for this simultaneous turn
            self.game.run_turn(self.action_r, self.action_b)

            # Clear stored actions
            self.action_r = None
            self.action_b = None

            # --- State AFTER the turn ---
            health_r = self.game.game_state.player_base_r.health
            health_b = self.game.game_state.player_base_b.health
            money_r  = self.game.game_state.money_r
            money_b  = self.game.game_state.money_b

            house_cost_r    = self.game.game_state.house_price_r
            house_cost_b    = self.game.game_state.house_price_b
            crossbow_cost_r = self.game.game_state.crossbow_price_r
            crossbow_cost_b = self.game.game_state.crossbow_price_b
            cannon_cost_r   = self.game.game_state.cannon_price_r
            cannon_cost_b   = self.game.game_state.cannon_price_b
            minigun_cost_r  = self.game.game_state.minigun_price_r
            minigun_cost_b  = self.game.game_state.minigun_price_b
            church_cost_r   = self.game.game_state.church_price_r
            church_cost_b   = self.game.game_state.church_price_b

            # --- Detect which towers actually got built (prices usually increase on purchase) ---
            house_built_r    = (house_cost_r    != old_house_cost_r)
            house_built_b    = (house_cost_b    != old_house_cost_b)
            crossbow_built_r = (crossbow_cost_r != old_crossbow_cost_r)
            crossbow_built_b = (crossbow_cost_b != old_crossbow_cost_b)
            cannon_built_r   = (cannon_cost_r   != old_cannon_cost_r)
            cannon_built_b   = (cannon_cost_b   != old_cannon_cost_b)
            minigun_built_r  = (minigun_cost_r  != old_minigun_cost_r)
            minigun_built_b  = (minigun_cost_b  != old_minigun_cost_b)
            church_built_r   = (church_cost_r   != old_church_cost_r)
            church_built_b   = (church_cost_b   != old_church_cost_b)

            # ======================
            #   REWARD COMPONENTS
            # ======================

            # 1. HEALTH-BASED (primary objective)
            # How much more did I damage the opponent than they damaged me?
            health_delta_r = health_r - old_health_r
            health_delta_b = health_b - old_health_b

            # 2. ECONOMY (secondary)
            income_r = money_r - old_money_r
            income_b = money_b - old_money_b

            # 3. TIME PENALTY (encourage faster games)
            time_penalty = -0.01

            # 4. ACTION-SPECIFIC SHAPING
            build_reward_r = 0.0
            build_reward_b = 0.0
            action_penalty_r = 0.0
            action_penalty_b = 0.0

            # ---- RED: rewards for actually building towers ----
            if house_built_r:
                build_reward_r += 0.6   # eco
            if crossbow_built_r:
                build_reward_r += 0.8   # basic defense
            if cannon_built_r:
                build_reward_r += 1.0   # strong splash
            if minigun_built_r:
                build_reward_r += 1.2   # high DPS
            if church_built_r:
                build_reward_r += 0.5   # support

            # ---- BLUE: same structure ----
            if house_built_b:
                build_reward_b += 0.6
            if crossbow_built_b:
                build_reward_b += 0.8
            if cannon_built_b:
                build_reward_b += 1.0
            if minigun_built_b:
                build_reward_b += 1.2
            if church_built_b:
                build_reward_b += 0.5

            # ---- RED: penalties for destroy and merc usage ----
            if old_action_r.action == "destroy":
                action_penalty_r -= 0.5  # discourage destroy as a default move

            # Mercs only come from "nothing" + direction; penalize that usage
            if old_action_r.action == "nothing" and old_action_r.merc_direction != "":
                action_penalty_r -= 0.3   # merc usage penalty
            elif old_action_r.action == "nothing" and old_action_r.merc_direction == "":
                action_penalty_r += 0.05  # mild reward for truly doing nothing (saving money / patience)

            # ---- BLUE: same penalties ----
            if old_action_b.action == "destroy":
                action_penalty_b -= 0.5

            if old_action_b.action == "nothing" and old_action_b.merc_direction != "":
                action_penalty_b -= 0.3
            elif old_action_b.action == "nothing" and old_action_b.merc_direction == "":
                action_penalty_b += 0.05

            # ======================
            #   FINAL REWARD
            # ======================
            w_health = 0.5
            o_health = -0.4
            w_econ   = 0.05

            reward_r = (
                w_health * health_delta_r +
                o_health * health_delta_b +
                w_econ * income_r +
                time_penalty +
                build_reward_r +
                action_penalty_r
            )

            reward_b = (
                w_health * health_delta_b +
                o_health * health_delta_r +
                w_econ * income_b +
                time_penalty +
                build_reward_b +
                action_penalty_b
            )

            # Accumulate rewards
            self.rewards["player_r"] = reward_r
            self.rewards["player_b"] = reward_b

            # --- Terminal large win/loss reward ---
            if self.game.game_state.is_game_over():
                if self.game.game_state.victory == 'r':
                    self.rewards["player_r"] += 200.0
                    self.rewards["player_b"] -= 200.0
                elif self.game.game_state.victory == 'b':
                    self.rewards["player_b"] += 200.0
                    self.rewards["player_r"] -= 200.0

                self.terminations = {a: True for a in self.agents}

            # PettingZoo cumulative rewards
            for a in self.agents:
                self._cumulative_rewards[a] = self.rewards[a]

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
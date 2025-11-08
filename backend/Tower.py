import math
import random

from Entity import Entity
from Mercenary import Mercenary
from GameState import GameState
from PlayerBase import PlayerBase
from Demon import Demon
from Utils import log_msg

class Tower(Entity):
    def __init__(
        self,
        x: int,
        y: int,
        team_color: str,
        cooldown: int,
        range : int,
        attack_pow : int,
        price: int,
        game_state: GameState
    ):
        super().__init__(1,x,y)
        self.cooldown_max = cooldown
        self.current_cooldown = self.cooldown_max
        self.tower_range = range
        self.attack_pow = attack_pow
        self.price = price
        # self.angle = 0

        self.targets = [] ##Keep track of all the positions it's targeting, instead of the angle

        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Tower team_color must be 'r' or 'b'") # TF2 reference?
        
        self.path = self.find_all_paths_in_range(game_state)
    

    # Called everytime the tower is updated
    def update(self, game_state: GameState):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
            self.targets = []
        else:
            self.tower_activation(game_state)
    

    def tower_activation(self, game_state: GameState):
        log_msg("Unimplemented tower_activation function!") # override in subclass

    def get_adjacent_targets(self, target, game_state: GameState):
        ahead_pos = target.get_adjacent_path_tile(game_state, +1)
        ahead_ent = game_state.entity_grid[ahead_pos[1]][ahead_pos[0]]
        
        behind_pos = target.get_adjacent_path_tile(game_state, -1)
        behind_ent = game_state.entity_grid[behind_pos[1]][behind_pos[0]]

        if isinstance(ahead_ent, Mercenary) and ahead_ent.team != self.team:
            ahead_ent.health -= self.attack_pow
        elif isinstance(behind_ent, Mercenary) and behind_ent.team != self.team:
            behind_ent.health -= self.attack_pow

    def shoot_single_priority_target(self, game_state: GameState, do_splash_damage=False):
        potential_targets = []

        for path in self.path:
            whats_on_path = game_state.entity_grid[path[1]][path[0]]

            if whats_on_path is None: continue
            if isinstance(whats_on_path, Mercenary):
                if whats_on_path.team != self.team:
                    potential_targets.append(whats_on_path)
            elif isinstance(whats_on_path, Demon):
                if whats_on_path.target_team == self.team:
                    potential_targets.append(whats_on_path)
        
        if len(potential_targets) == 0: return

        # Try to select the closest target to the base first
        # If targets are tied by closeness to the base, try to select the target with the most health
        # If targets are tied by health, try to select the target with the highest attack power
        # If still tied, do a random tiebreaker
        potential_targets.sort(key=lambda ent: (
            -ent.current_path.index((ent.x, ent.y)) if self.team == 'b' else ent.current_path.index((ent.x, ent.y)),
            -ent.health,
            -ent.attack_pow,
            random.random()
        ))

        target = potential_targets[0]
        target.health -= self.attack_pow
        self.current_cooldown = self.cooldown_max
        self.targets.append((target.x, target.y))
        # self.angle = math.atan2(path[1] - self.y, path[0] - self.x)

<<<<<<< HEAD
        if do_splash_damage:
            self.get_adjacent_targets(self, target, game_state)
            # Check for the surrounding tiles to see if enemy mercs are there, and damage them as well

=======
        self.last_hit_targets = [(target.x, target.y)]
>>>>>>> 9acced6803b24f572aaacef1924f44334b95a1da
        log_msg(f'Tower {self.name} hit {target.name} for {self.attack_pow} damage')


    def shoot_all_targets_in_range(self, game_state: GameState):

        hit_targets = []

        for path in self.path:
            whats_on_path = game_state.entity_grid[path[1]][path[0]]

            if whats_on_path is None: continue
            if ((isinstance(whats_on_path, Mercenary) and whats_on_path.team != self.team) or
                (isinstance(whats_on_path, Demon) and whats_on_path.target_team == self.team)):

                whats_on_path.health -= self.attack_pow
                self.targets.append((whats_on_path.x, whats_on_path.y))
                # self.angle = math.atan2(path[1] - self.y, path[0] - self.x)

                hit_targets.append((whats_on_path.x, whats_on_path.y))
                log_msg(f'Tower {self.name} hit {whats_on_path.name} for {self.attack_pow} damage')
            
            self.current_cooldown = self.cooldown_max
        
        if len(hit_targets) != 0:
            self.last_hit_targets = hit_targets


    def find_all_paths_in_range(self, game_state: GameState) -> list:
        paths = []

        floor_tiles = game_state.floor_tiles

        for xi in range(self.x - self.tower_range, self.x + self.tower_range):
            for yi in range(self.y - self.tower_range, self.y + self.tower_range):
                if xi == self.x and yi == self.y: continue
                if game_state.is_out_of_bounds(xi,yi): continue

                # This is the circle equation, I like my tower range to be circles
                if math.sqrt((xi - self.x) * (xi - self.x) + (yi - self.y) * (yi - self.y)) <= self.tower_range:
                    # We're using the tile grid since we don't need to know the entities to know where a path is
                    if floor_tiles[yi][xi] == 'O':
                        paths.append((xi,yi))

        return paths

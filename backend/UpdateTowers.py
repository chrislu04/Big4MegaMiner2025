from GameState import GameState
from Tower import Tower
from House import House
from Cannon import Cannon
from Minigun import Minigun
from Crossbow import Crossbow
import Constants

def update_towers(game_state: GameState):
    towers = game_state.towers

    # Iterates through the tower list, and lowers the cooldown for each appropriate type
    for tower in towers:
        current_cooldown = tower.current_cooldown
        current_team = tower.team_color

        ## House Tower activation
        if isinstance(tower, House):
            if current_cooldown > 0:
                current_cooldown -= 1
            else:
                if current_team == 'r':
                    game_state.money_r += Constants.HOUSE_MONEY_PRODUCED
                else:
                    game_state.money_b += Constants.HOUSE_MONEY_PRODUCED
                tower.current_cooldown = Constants.HOUSE_MAX_COOLDOWN

        ## Cannon Tower activation
        elif isinstance(tower, Cannon):
            if current_cooldown > 0:
                current_cooldown -= 1
            else:
                enemies_in_range = find_all_enemies_in_range(game_state, tower.x, tower.y, current_team, Constants.CANNON_RANGE)
                if len(enemies_in_range) > 0:
                    # Attack the highest-priority enemy
                    highest_priority = enemies_in_range[0]
                    highest_priority.health -= Constants.CANNON_DAMAGE
                    tower.current_cooldown = Constants.CANNON_MAX_COOLDOWN

        ## Crossbow Tower activation
        elif isinstance(tower, Crossbow):
            if current_cooldown > 0:
                current_cooldown -= 1
            else:
                enemies_in_range = find_all_enemies_in_range(game_state, tower.x, tower.y, current_team, Constants.CROSSBOW_RANGE)
                if len(enemies_in_range) > 0:
                    # Attack the highest-priority enemy
                    highest_priority = enemies_in_range[0]
                    highest_priority.health -= Constants.CROSSBOW_DAMAGE
                    tower.current_cooldown = Constants.CROSSBOW_MAX_COOLDOWN
        
        ## Minigun Tower activation
        elif isinstance(tower, Minigun):
            if current_cooldown > 0:
                current_cooldown -= 1
            else:
                enemies_in_range = find_all_enemies_in_range(game_state, tower.x, tower.y, current_team, Constants.MINIGUN_RANGE)
                if len(enemies_in_range) > 0:
                    # Attack all enemies in range
                    for enemy in enemies_in_range:
                        enemy.health -= Constants.MINIGUN_DAMAGE
                    tower.current_cooldown = Constants.MINIGUN_MAX_COOLDOWN

# Ordered by priority of attack
# TODO: figure out what this priority is, and put that in the rules
def find_all_enemies_in_range(game_state: GameState, x: int, y: int, team_color: str, range: int) -> list:
    pass # TODO
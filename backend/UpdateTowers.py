from GameState import GameState
from Tower import Tower
from House import House
from Cannon import Cannon
from Minigun import Minigun
from Crossbow import Crossbow
from Demon import Demon
from Mercenary import Mercenary
import Constants

def update_towers(game_state: GameState):
    towers = game_state.towers

    # Iterates through the tower list, and lowers the cooldown for each appropriate type
    for tower in towers:
        if isinstance(tower, House):
            tower.update(game_state) ##House really only needs money_r and money_b, but we can only change those values if we give it the whole game_state

        if isinstance(tower, Tower): ## I would hope that the towers list only have towers in it
            tower.update(game_state.entity_grid)
        
        # current_cooldown = tower.current_cooldown
        # current_team = tower.team_color

        # ## House Tower activation
        # if isinstance(tower, House):
        #     if current_cooldown > 0:
        #         current_cooldown -= 1
        #     else:
        #         if current_team == 'r':
        #             game_state.money_r += Constants.HOUSE_MONEY_PRODUCED
        #         else:
        #             game_state.money_b += Constants.HOUSE_MONEY_PRODUCED
        #         tower.current_cooldown = Constants.HOUSE_MAX_COOLDOWN

        # ## Cannon Tower activation
        # elif isinstance(tower, Cannon):
        #     if current_cooldown > 0:
        #         current_cooldown -= 1
        #     else:
        #         enemies_in_range = find_all_enemies_in_range(game_state, tower.x, tower.y, current_team, Constants.CANNON_RANGE)
        #         if len(enemies_in_range) > 0:
        #             # Attack the highest-priority enemy
        #             highest_priority = enemies_in_range[0]
        #             highest_priority.health -= Constants.CANNON_DAMAGE
        #             tower.current_cooldown = Constants.CANNON_MAX_COOLDOWN

        # ## Crossbow Tower activation
        # elif isinstance(tower, Crossbow):
        #     if current_cooldown > 0:
        #         current_cooldown -= 1
        #     else:
        #         enemies_in_range = find_all_enemies_in_range(game_state, tower.x, tower.y, current_team, Constants.CROSSBOW_RANGE)
        #         if len(enemies_in_range) > 0:
        #             # Attack the highest-priority enemy
        #             highest_priority = enemies_in_range[0]
        #             highest_priority.health -= Constants.CROSSBOW_DAMAGE
        #             tower.current_cooldown = Constants.CROSSBOW_MAX_COOLDOWN
        
        # ## Minigun Tower activation
        # elif isinstance(tower, Minigun):
        #     if current_cooldown > 0:
        #         current_cooldown -= 1
        #     else:
        #         enemies_in_range = find_all_enemies_in_range(game_state, tower.x, tower.y, current_team, Constants.MINIGUN_RANGE)
        #         if len(enemies_in_range) > 0:
        #             # Attack all enemies in range
        #             for enemy in enemies_in_range:
        #                 enemy.health -= Constants.MINIGUN_DAMAGE
        #             tower.current_cooldown = Constants.MINIGUN_MAX_COOLDOWN

# # Ordered by priority of attack
# # TODO: figure out what this priority is, and put that in the rules
# # Priority should be enemies closest to the base, and if enemies are equadistant, then priority should go to lower healthed one
# def find_all_enemies_in_range(game_state: GameState, x: int, y: int, team_color: str, max_dist: int) -> list:
#     enemies = []
#     for xi in range(x-max_dist,x+max_dist):
#         for yi in range(y-max_dist,y+max_dist):
#             if xi == x and yi == y: continue
            
#             # get the entity at each position in range
#             entity = game_state.entity_grid[xi][yi]

#             # demons are always enemies
#             if isinstance(entity, Demon):
#                 enemies.append(entity)
            
#             # shoot enemy mercs
#             elif isinstance(entity, Mercenary):
#                 if entity.team_color != team_color:
#                     enemies.append(entity)
    
#     # TODO: sort these based on priority
#     return enemies
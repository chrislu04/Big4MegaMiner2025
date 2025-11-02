from typing import List
from GameState import GameState
from Demon import Demon
from PlayerBase import PlayerBase
from Mercenary import Mercenary
from Entity import Entity
import Constants

def update_demons(game_state: GameState):
    # Determine all demon states
    moving: List[Demon] = []
    fighting: List[Demon] = []
    waiting: List[Demon] = []
    set_all_demon_states(game_state, game_state.demons, moving, fighting, waiting)

    # Move all demons in moving state
    move_all_demons(game_state, moving)

    # Apply combat effects for all demons in fighting state
    for demon in fighting:
        do_demon_combat_single(game_state, demon)

# Side effect: All demon objects will have their state set appropiately
# Side effect: moving, fighting and waiting lists will be populated
def set_all_demon_states(game_state: GameState, demons: List[Demon], 
                        moving: List[Demon],
                        fighting: List[Demon],
                        waiting: List[Demon]):
    for demon in demons:
        next_tile1 = demon.get_adjacent_path_tile(game_state, 1)
        next_tile2 = demon.get_adjacent_path_tile(game_state, 2)
        blocking_entity1 = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
        blocking_entity2 = game_state.entity_grid[next_tile2[1]][next_tile2[0]]

        # fighting if rival merc or demon or player base is within 1 space
        if (demon.get_attackable_player_base(game_state) != None or
            type(blocking_entity1) == type(Mercenary) or 
            (type(blocking_entity1) == type(Demon) and blocking_entity1.target_team != demon.team)):
            demon.state = 'fighting'
            # set all demons behind us to waiting
            demon.set_behind_waiting(game_state)
        # fighting if enemy is within 2 spaces and merc within 1 space is not ally
        elif (type(blocking_entity1) == None and
            type(blocking_entity2) == type(Demon) or
            (type(blocking_entity2) == type(Mercenary) and blocking_entity2.team != demon.team)):
            demon.state = 'fighting'
            # set all demons behind us to waiting
            demon.set_behind_waiting(game_state)
        # if not waiting or fighting, then moving
        elif demon.state != 'waiting':
            demon.state = 'moving'
        
        # add to correct list
        if demon.state == 'fighting': fighting.append(demon)
        if demon.state == 'waiting': waiting.append(demon)
        if demon.state == 'moving': moving.append(demon)

def move_all_demons(game_state: GameState, demons: List[Demon]):
    # remove moving demons
    for demon in demons:
        game_state.entity_grid[demon.y][demon.x] = None

    # set new position
    for demon in demons:
        new_pos = demon.get_adjacent_path_tile(game_state, 1)
        demon.x = new_pos[0]
        demon.y = new_pos[1]

    # add moving demons back
    for demon in demons:
        game_state.entity_grid[demon.y][demon.x] = demon

def do_demon_combat_single(game_state: GameState, demon: Demon):
    next_tile1 = demon.get_adjacent_path_tile(game_state, 1)
    next_tile2 = demon.get_adjacent_path_tile(game_state, 2)
    target1: Entity = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
    target2: Entity = game_state.entity_grid[next_tile2[1]][next_tile2[0]]
    
    # if tile 1 space in front is empty, we are contesting space with enemy 2 spaces in front 
    if target1 != None:
        target1.health -= Constants.DEMON_ATTACK_POWER
    elif target2 != None:
        target2.health -= Constants.DEMON_ATTACK_POWER
    
    # attack the player base if we have reached the end of the path
    attackable_base = demon.get_attackable_player_base(game_state)
    if attackable_base != None:
        attackable_base.health -= Constants.DEMON_ATTACK_POWER
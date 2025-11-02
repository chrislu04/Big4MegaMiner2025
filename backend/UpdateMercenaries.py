import math
from typing import List
from GameState import GameState
from Mercenary import Mercenary
from Demon import Demon
from PlayerBase import PlayerBase
from Entity import Entity
import Constants

def update_mercenaries(game_state: GameState):
    # Determine all merc states
    moving: List[Mercenary] = []
    fighting: List[Mercenary] = []
    waiting: List[Mercenary] = []
    set_all_merc_states(game_state, game_state.mercs, moving, fighting, waiting)

    # Move all mercs in moving state
    move_all_mercs(game_state, moving)

    # Apply combat effects for all mercs in fighting state
    for merc in fighting:
        do_merc_combat_single(game_state, merc)

# Side effect: All merc objects will have their state set appropiately
# Side effect: moving, fighting and waiting lists will be populated
def set_all_merc_states(game_state: GameState, mercs: List[Mercenary], 
                        moving: List[Mercenary],
                        fighting: List[Mercenary],
                        waiting: List[Mercenary]):
    for merc in mercs:
        next_tile1 = merc.get_adjacent_path_tile(game_state, 1)
        next_tile2 = merc.get_adjacent_path_tile(game_state, 2)
        blocking_entity1 = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
        blocking_entity2 = game_state.entity_grid[next_tile2[1]][next_tile2[0]]

        # fighting if rival merc or demon or player base is within 1 space
        if (merc.get_attackable_player_base(game_state) != None or
            type(blocking_entity1) == type(Demon) or
            (type(blocking_entity1) == type(Mercenary) and blocking_entity1.team != merc.team)):
            merc.state = 'fighting'
            # set all mercs behind us to waiting
            merc.set_behind_waiting(game_state)
        # fighting if enemy is within 2 spaces and merc within 1 space is not ally
        elif (type(blocking_entity1) == None and
            type(blocking_entity2) == type(Demon) or
            (type(blocking_entity2) == type(Mercenary) and blocking_entity2.team != merc.team)):
            merc.state = 'fighting'
            # set all mercs behind us to waiting
            merc.set_behind_waiting(game_state)
        # if not waiting or fighting, then moving
        elif merc.state != 'waiting':
            merc.state = 'moving'
        
        # add to correct list
        if merc.state == 'fighting': fighting.append(merc)
        if merc.state == 'waiting': waiting.append(merc)
        if merc.state == 'moving': moving.append(merc)

def move_all_mercs(game_state: GameState, mercs: List[Mercenary]):
    # remove moving mercs
    for merc in mercs:
        game_state.entity_grid[merc.y][merc.x] = None

    # set new position
    for merc in mercs:
        new_pos = merc.get_adjacent_path_tile(game_state, 1)
        merc.x = new_pos[0]
        merc.y = new_pos[1]

    # add moving mercs back
    for merc in mercs:
        game_state.entity_grid[merc.y][merc.x] = merc

def do_merc_combat_single(game_state: GameState, merc: Mercenary):
    next_tile1 = merc.get_adjacent_path_tile(game_state, 1)
    next_tile2 = merc.get_adjacent_path_tile(game_state, 2)
    target1: Entity = game_state.entity_grid[next_tile1[1]][next_tile1[0]]
    target2: Entity = game_state.entity_grid[next_tile2[1]][next_tile2[0]]
    
    # if tile 1 space in front is empty, we are contesting space with enemy 2 spaces in front 
    if target1 != None:
        target1.health -= Constants.MERCENARY_ATTACK_POWER
    elif target2 != None:
        target2.health -= Constants.MERCENARY_ATTACK_POWER
# Phase 3 | Updates everything, making things move/attack and determining win/lose

from GameState import GameState
from UpdateMercenaries import update_mercenaries
from UpdateDemons import update_demons
from SpawnMercenaries import spawn_mercenaries
from SpawnDemons import spawn_demons

def world_update_phase(game_state: GameState):
    update_mercenaries(game_state)
    check_wincon(game_state)

    update_demons(game_state)
    check_wincon(game_state)
    
    spawn_mercenaries(game_state)
    spawn_demons(game_state)

def check_wincon(game_state: GameState):
    pass # TODO
from GameState import GameState
from Mercenary import Mercenary

def spawn_mercenaries(game_state: GameState):

    bx = game_state.player_base_r.x
    by = game_state.player_base_r.y

    if game_state.player_base_r.mercenary_queued_up > 0 and game_state.entity_grid[bx][by - 2]:
        game_state.entity_grid[bx][by - 2] = Mercenary(bx, by, "r")

    if game_state.player_base_r.mercenary_queued_down > 0 and game_state.entity_grid[bx][by + 2]:
        game_state.entity_grid[bx][by + 2] = Mercenary(bx, by, "r")

    if game_state.player_base_r.mercenary_queued_left > 0 and game_state.entity_grid[bx - 2][by]:
        game_state.entity_grid[bx - 2][by] = Mercenary(bx - 2, by, "r")

    if game_state.player_base_r.mercenary_queued_right > 0 and game_state.entity_grid[bx + 2][by]:
        game_state.entity_grid[bx + 2][by] = Mercenary(bx + 2, by, "r")

    bx = game_state.player_base_b.x
    by = game_state.player_base_b.y
    
    if game_state.player_base_b.mercenary_queued_up > 0 and game_state.entity_grid[bx][by - 2] == None:

        game_state.entity_grid[bx][by - 2] = Mercenary(bx, by - 2, "b", "blah blah why is this in the constructor")
        game_state.mercs.append(game_state.entity_grid[bx][by - 2])
        game_state.player_base_b.mercenary_queued_up -= 1
        

    if game_state.player_base_b.mercenary_queued_down > 0 and game_state.entity_grid[bx][by + 2]:
        game_state.entity_grid[bx][by + 2] = Mercenary(bx, by, "b")

    if game_state.player_base_b.mercenary_queued_left > 0 and game_state.entity_grid[bx - 2][by]:
        game_state.entity_grid[bx - 2][by] = Mercenary(bx, by, "b")

    if game_state.player_base_b.mercenary_queued_right > 0 and game_state.entity_grid[bx + 2][by]:
        game_state.entity_grid[bx + 2][by] = Mercenary(bx, by, "b")


    
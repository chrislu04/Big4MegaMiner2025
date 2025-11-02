from GameState import GameState
from Mercenary import Mercenary

def spawn_single_mercenary(game_state: GameState, x: int, y: int, team_color: str):
    merc = Mercenary(x, y, team_color, game_state)
    game_state.entity_grid[y][x] = merc
    game_state.mercs.append(merc)


def spawn_mercenaries(game_state: GameState):

    bx = game_state.player_base_r.x
    by = game_state.player_base_r.y

    if game_state.player_base_r.mercenary_queued_up > 0 and game_state.entity_grid[by - 2][bx] == None:
        spawn_single_mercenary(game_state, bx, by - 2, "r")
        game_state.player_base_r.mercenary_queued_up = 0

    if game_state.player_base_r.mercenary_queued_down > 0 and game_state.entity_grid[by + 2][bx] == None:
        spawn_single_mercenary(game_state, bx, by + 2, "r")
        game_state.player_base_r.mercenary_queued_down = 0

    if game_state.player_base_r.mercenary_queued_left > 0 and game_state.entity_grid[by][bx - 2] == None:
        spawn_single_mercenary(game_state, bx - 2, by, "r")
        game_state.player_base_r.mercenary_queued_left = 0

    if game_state.player_base_r.mercenary_queued_right > 0 and game_state.entity_grid[by][bx + 2] == None:
        spawn_single_mercenary(game_state, bx + 2, by, "r")
        game_state.player_base_r.mercenary_queued_right = 0


    bx = game_state.player_base_b.x
    by = game_state.player_base_b.y
    
    if game_state.player_base_r.mercenary_queued_up > 0 and game_state.entity_grid[by - 2][bx] == None:
        spawn_single_mercenary(game_state, bx, by - 2, "b")
        game_state.player_base_r.mercenary_queued_up = 0

    if game_state.player_base_r.mercenary_queued_down > 0 and game_state.entity_grid[by + 2][bx] == None:
        spawn_single_mercenary(game_state, bx, by + 2, "b")
        game_state.player_base_r.mercenary_queued_down = 0

    if game_state.player_base_r.mercenary_queued_left > 0 and game_state.entity_grid[by][bx - 2] == None:
        spawn_single_mercenary(game_state, bx - 2, by, "b")
        game_state.player_base_r.mercenary_queued_left = 0

    if game_state.player_base_r.mercenary_queued_right > 0 and game_state.entity_grid[by][bx + 2] == None:
        spawn_single_mercenary(game_state, bx + 2, by, "b")
        game_state.player_base_r.mercenary_queued_right = 0


    
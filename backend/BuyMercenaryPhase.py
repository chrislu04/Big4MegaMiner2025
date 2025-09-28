# Phase 2 | Manages buying mercs

def buy_mercenary_phase(game_state: GameState, ai_action: AIAction) -> None:
    # Make sure:
    # 1: enough money
    # 2: there is not already a merc queued in that direction
    # 3: there is a path tile in that direction

    if ai_action.action_r.buy_mercenary:
        pbr = game_state.player_base_r

        if game_state.money_r < 20:
            raise Exception("Not enough money!")
        else:

            if ai_action.action_r.direction == "up" \
            and pbr.mercenary_queued_up == False \
            and game_state.tile_grid[pbr.x][pbr.y - 1] == "path":
                pbr.mercenary_queued_up = True
                game_state.money_r -= 20
            
            elif ai_action.action_r.direction == "down" \
            and pbr.mercenary_queued_down == False \
            and game_state.tile_grid[pbr.x][pbr.y + 1] == "path":
                pbr.mercenary_queued_down = True
                game_state.money_r -= 20
            
            elif ai_action.action_r.direction == "left" \
            and pbr.mercenary_queued_left == False \
            and game_state.tile_grid[pbr.x - 1][pbr.y] == "path":
                pbr.mercenary_queued_left = True
                game_state.money_r -= 20
            
            elif ai_action.action_r.direction == "right" \
            and pbr.mercenary_queued_right == False \
            and game_state.tile_grid[pbr.x + 1][pbr.y] == "path":
                pbr.mercenary_queued_right = True
                game_state.money_r -= 20
            
            else: raise Exception("Invalid direction specified!")

    if ai_action.action_l.buy_mercenary:
        pbl = game_state.player_base_l

        if game_state.money_l < 20:
            raise Exception("Not enough money!")
        else:

            if ai_action.action_l.direction == "up" \
            and pbl.mercenary_queued_up == False \
            and game_state.tile_grid[pbl.x][pbl.y - 1] == "path":
                pbl.mercenary_queued_up = True
                game_state.money_l -= 20
            
            elif ai_action.action_l.direction == "down" \
            and pbl.mercenary_queued_down == False \
            and game_state.tile_grid[pbl.x][pbl.y + 1] == "path":
                pbl.mercenary_queued_down = True
                game_state.money_l -= 20
            
            elif ai_action.action_l.direction == "left" \
            and pbl.mercenary_queued_left == False \
            and game_state.tile_grid[pbl.x - 1][pbl.y] == "path":
                pbl.mercenary_queued_left = True
                game_state.money_l -= 20
            
            elif ai_action.action_l.direction == "right" \
            and pbl.mercenary_queued_right == False \
            and game_state.tile_grid[pbl.x + 1][pbl.y] == "path":
                pbl.mercenary_queued_right = True
                game_state.money_l -= 20
            
            else: raise Exception("Invalid direction specified!")
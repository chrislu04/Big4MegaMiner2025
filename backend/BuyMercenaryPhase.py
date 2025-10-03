from GameState import GameState
from AIAction import AIAction
# Phase 2 | Manages buying mercs

def buy_mercenary_phase(game_state: GameState, ai_action_r: AIAction, ai_action_b : AIAction) -> None:
    # Make sure:
    # 1: enough money
    # 2: there is not already a merc queued in that direction
    # 3: there is a path tile in that direction

    if ai_action_r.queue_merc_action:
        pbr = game_state.player_base_r

        if game_state.money_r < 20:
            raise Exception("Not enough money!")
        else:
            print("red player bougt merc")
            if ai_action_r.queue_direction == "up" \
            and pbr.mercenary_queued_up == False \
            and game_state.tile_grid[pbr.x][pbr.y - 2] == "path":
                pbr.mercenary_queued_up += 1
                game_state.money_r -= 20
            
            elif ai_action_r.queue_direction == "down" \
            and pbr.mercenary_queued_down == False \
            and game_state.tile_grid[pbr.x][pbr.y + 2] == "path":
                pbr.mercenary_queued_down += 1
                game_state.money_r -= 20
            
            elif ai_action_r.queue_direction == "left" \
            and pbr.mercenary_queued_left == False \
            and game_state.tile_grid[pbr.x - 2][pbr.y] == "path":
                pbr.mercenary_queued_left += 1
                game_state.money_r -= 20
            
            elif ai_action_r.queue_direction == "right" \
            and pbr.mercenary_queued_right == False \
            and game_state.tile_grid[pbr.x + 2][pbr.y] == "path":
                pbr.mercenary_queued_right += 1
                game_state.money_r -= 20
            
            else: raise Exception("Invalid direction specified!")

    if ai_action_b.queue_merc_action:
        pbl = game_state.player_base_b

        if game_state.money_b < 20:
            pass #raise Exception("Not enough money!") <== removing this more
        else:
            if (ai_action_b.queue_direction == "up" 
                # and pbl.mercenary_queued_up == True
                and game_state.tile_grid[pbl.x][pbl.y - 2] == "Path"):
                pbl.mercenary_queued_up += 1
                game_state.money_b -= 20
            
            elif (ai_action_b.queue_direction == "down"
                #and pbl.mercenary_queued_down == False
                and game_state.tile_grid[pbl.x][pbl.y + 2] == "path"):
                pbl.mercenary_queued_down += 1
                game_state.money_b -= 20
            
            elif (ai_action_b.queue_direction == "left"
               # and pbl.mercenary_queued_left == False
                and game_state.tile_grid[pbl.x - 2][pbl.y] == "path"):
                pbl.mercenary_queued_left += 1
                game_state.money_b -= 20
            
            elif (ai_action_b.queue_direction == "right"
                #and pbl.mercenary_queued_right == False
                and game_state.tile_grid[pbl.x + 2][pbl.y] == "path"):
                pbl.mercenary_queued_right += 1
                game_state.money_b -= 20
            
            else: raise Exception("Invalid direction specified!")
from GameState import GameState
# Need to import AIAction still (?)
# Do we need to import these here or no?

# Phase 1 | Manages building towers and such

def build_tower_phase(x: int, y: int, game_state: GameState, ai_action: AIAction) -> None:
    # Make sure:
    # 1: enough money
    # 2: the space chosen is open

    if ai_action.action_r.build_tower:
        x = None # x that is selected to be built at
        y = None # y that is selected to be built at

        # Need to further define the Tower and Tower subclasses to fully
        # set up the rest of this phase, mainly for detection of which
        # tower has been chosen to be built

        # If the tower being built is the house :
        if game_state.money_r < 10:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("house")
            game_state.tile_grid[x, y] == "house" # Update the grid to represent the newly built tower at the correct position
            game_state.money_r -= 10

        # If the tower being built is the cannon :
        if game_state.money_r < 10:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("cannon")
            game_state.tile_grid[x, y] == "cannon" # Update the grid to represent the newly built tower at the correct position
            game_state.money_r -= 10

        # If the tower being built is the minigun :
        if game_state.money_r < 25:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("minigun")
            game_state.tile_grid[x, y] == "minigun" # Update the grid to represent the newly built tower at the correct position
            game_state.money_r -= 25

            # If the tower being built is the crossbow :
        if game_state.money_r < 8:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("crossbow")
            game_state.tile_grid[x, y] == "crossbow" # Update the grid to represent the newly built tower at the correct position
            game_state.money_r -= 8


    ## --- BLUE TEAM TOWERS --- ##

    if ai_action.action_b.build_tower:
        x = None # x that is selected to be built at
        y = None # y that is selected to be built at

        # Need to further define the Tower and Tower subclasses to fully
        # set up the rest of this phase, mainly for detection of which
        # tower has been chosen to be built

        # If the tower being built is the house :
        if game_state.money_b < 10:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("house")
            game_state.tile_grid[x, y] == "house" # Update the grid to represent the newly built tower at the correct position
            game_state.money_b -= 10

        # If the tower being built is the cannon :
        if game_state.money_b < 10:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("cannon")
            game_state.tile_grid[x, y] == "cannon" # Update the grid to represent the newly built tower at the correct position
            game_state.money_b -= 10

        # If the tower being built is the minigun :
        if game_state.money_r < 25:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("minigun")
            game_state.tile_grid[x, y] == "minigun" # Update the grid to represent the newly built tower at the correct position
            game_state.money_b -= 25

            # If the tower being built is the crossbow :
        if game_state.money_b < 8:
            raise Exception("Not enough money!")
        else:
        
            game_state.towers.append("crossbow")
            game_state.tile_grid[x, y] == "crossbow" # Update the grid to represent the newly built tower at the correct position
            game_state.money_b -= 8
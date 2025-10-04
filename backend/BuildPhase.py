from GameState import GameState
from AIAction import AIAction 
from Tower import Tower
from Cannon import Cannon
from Crossbow import Crossbow
from House import House
from Minigun import Minigun

# Phase 1 | Manages building towers and such

def build_tower_phase(game_state: GameState, ai_action_r: AIAction, ai_action_b : AIAction) -> None:
    # Make sure:
    # 1: enough money
    # 2: the space chosen is open

    x = ai_action_r.x # x that is selected to be built at
    y = ai_action_r.y # y that is selected to be built at
    
    ## Check if the buy action was called, then check if the tile is valid (within same territory), then check if nothing else is on the tower
    if ai_action_r.buy_tower_action and game_state.tile_grid[x][y] == "r" and game_state.entity_grid[x][y] is None:

        # Need to further define the Tower and Tower subclasses to fully
        # set up the rest of this phase, mainly for detection of which
        # tower has been chosen to be built
        match ai_action_r.tower_to_build.lower():
            case "house":
                # If the tower being built is the house :
                house = House(x , y, "r")

                if game_state.money_r < house.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(house)
                    game_state.entity_grid[x, y] = house # Update the grid to represent the newly built tower at the correct position
                    game_state.money_r -= house.value
                    house.buildt(game_state.tile_grid)

            case "cannon":
                # If the tower being built is the cannon :
                cannon = Cannon(x , y, "r")

                if game_state.money_r < cannon.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(cannon)
                    game_state.entity_grid[x, y] = cannon # Update the grid to represent the newly built tower at the correct position
                    game_state.money_r -= cannon.value
                    cannon.buildt(game_state.tile_grid)

            case "minigun":
                # If the tower being built is the minigun :
                mini = Minigun(x , y, "r")

                if game_state.money_r < house.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(mini)
                    game_state.entity_grid[x, y] = mini # Update the grid to represent the newly built tower at the correct position
                    game_state.money_r -= mini.value
                    mini.buildt(game_state.tile_grid)
            case "crossbow":
                # If the tower being built is the crossbow :
                cross = Crossbow(x, y, team_color='r')

                if game_state.money_r < cross.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(cross)
                    game_state.entity_grid[x][y] = cross # Update the grid to represent the newly built tower at the correct position
                    game_state.money_r -= cross.value
                    cross.buildt(game_state.tile_grid)


    ## --- BLUE TEAM TOWERS --- ##
    x = ai_action_b.x # x that is selected to be built at
    y = ai_action_b.y

     ## Check if the buy action was called, then check if the tile is valid (within same territory), then check if nothing else is on the tower
    if ai_action_b.buy_tower_action and game_state.tile_grid[x][y] == "b" and not game_state.entity_grid[x][y] is None:

        # Need to further define the Tower and Tower subclasses to fully
        # set up the rest of this phase, mainly for detection of which
        # tower has been chosen to be built
        match ai_action_b.tower_to_build.lower():
            case "house":
                # If the tower being built is the house :
                house = House(x , y, "b")

                if game_state.money_b < house.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(house)
                    game_state.entity_grid[x, y] == house # Update the grid to represent the newly built tower at the correct position
                    game_state.money_b -= house.value
                    house.buildt(game_state.tile_grid)

            case "cannon":
                # If the tower being built is the house :
                cannon = Cannon(x , y, "b")

                if game_state.money_b < cannon.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(cannon)
                    game_state.entity_grid[x, y] == cannon # Update the grid to represent the newly built tower at the correct position
                    game_state.money_b -= cannon.value
                    cannon.buildt(game_state.tile_grid)

            case "minigun":
                # If the tower being built is the house :
                mini = Minigun(x , y, "b")

                if game_state.money_b < house.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(mini)
                    game_state.entity_grid[x, y] == mini # Update the grid to represent the newly built tower at the correct position
                    game_state.money_b -= mini.value
                    mini.buildt(game_state.tile_grid)
            case "crossbow":
                # If the tower being built is the house :
                cross = Crossbow(x , y, "b")

                if game_state.money_b < cross.value:
                    raise Exception("Not enough money!")
                else:
                    game_state.towers.append(cross)
                    game_state.entity_grid[x, y] == cross # Update the grid to represent the newly built tower at the correct position
                    game_state.money_b -= cross.value
                    cross.buildt(game_state.tile_grid)
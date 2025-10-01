# Phase 3 | Updates everything, making things move/attack and determining win/lose

from GameState import GameState
from UpdateMercenaries import update_mercenaries
from UpdateDemons import update_demons
from SpawnMercenaries import spawn_mercenaries
from SpawnDemons import spawn_demons
from House import House
from Cannon import Cannon
from Minigun import Minigun
import Constants

def world_update_phase(game_state: GameState):
    update_mercenaries(game_state)
    check_wincon(game_state)

    update_demons(game_state)
    check_wincon(game_state)
    
    spawn_mercenaries(game_state)
    spawn_demons(game_state)

def check_wincon(game_state: GameState):
    # Determines which player wins the game, if there is an current winner
    team_b_hp = game_state.player_base_b.hp
    team_r_hp = game_state.player_base_r.hp

    team_b_money = game_state.money_b
    team_r_money = game_state.money_r

    towers = game_state.towers

    ## If one player's base is Destroyed and the other is not, the player with the surviving base wins.
    if team_b_hp <= 0 or team_r_hp <= 0:
        if team_b_hp == 0:
            return "Team R is the winner!"
        elif team_r_hp == 0:
            return "Team B is the winner!"
        
    ## If both players' bases are Destroyed, break the tie based on who has the most Money.
    elif team_b_hp <= 0 and team_r_hp <= 0:
        if team_b_money != team_r_money:
            if team_b_money > team_r_money:
                return "Team B is the winner!"
            elif team_r_money > team_b_money:
                return "Team R is the winner!"
        else:
            ## Then, if both players have the same amount of Money, break the tie based on who has built the most towers.
            # Empty lists that will store each tower the teams have
            r_towers = []
            b_towers = []

            for tower in towers:
                current_team = towers.team_color
                if current_team == 'r':
                    r_towers.append(tower)
                else:
                    b_towers.append(tower)
            
            if len(r_towers) != len(b_towers):
                if len(r_towers) > len(b_towers):
                    return "Team R is the winner!"
                else:
                    return "Team B is the winner!"
            else:
                ## Then, if both players have built the same number of towers, break the tie based on the sum of prices of those towers.
                # Equals the total price of the total amount of towers per team
                r_total_cost = 0
                b_total_cost = 0
                current_team = tower.team_color

                for tower in r_towers:
                    if isinstance(tower, House):
                        if current_team == 'r':
                            r_total_cost += Constants.HOUSE_PRICE
                        else:
                            b_total_cost += Constants.HOUSE_PRICE
                    elif isinstance(tower, Cannon):
                        if current_team == 'r':
                            r_total_cost += Constants.CANNON_PRICE
                        else:
                            b_total_cost += Constants.CANNON_PRICE
                    elif isinstance(tower, Minigun):
                        if current_team == 'r':
                            r_total_cost += Constants.MINIGUN_PRICE
                        else:
                            b_total_cost += Constants.MINIGUN_PRICE
                    else:
                        if current_team == 'r':
                            r_total_cost += Constants.CROSSBOW_PRICE
                        else:
                            b_total_cost += Constants.CROSSBOW_PRICE
                if r_total_cost != b_total_cost:
                    if r_total_cost > b_total_cost:
                        return "Team R is the winner!"
                    else:
                        return "Team B is the winner!"
                else:
                    ##Then, if both sums are equal, break the tie based on the number of Mercenaries each player has.

                    # Number of mercenaries per team
                    r_mercs = 0
                    b_mercs = 0

                    for merc in game_state.mercs:
                        if merc.team_color == 'r':
                            r_mercs += 1
                        else:
                            b_mercs += 1
                    
                    if r_mercs != b_mercs:
                        if r_mercs > b_mercs:
                            return "Team R is the winner!"
                        else:
                            return "Team B is the winner!"
                    else:
                        ##Then, if both have the same number of Mercenaries, break the tie based on the sum of HP of mercenaries.
                        r_mercs_hp = 0
                        b_mercs_hp = 0

                        for merc in game_state.mercs:
                            if merc.team_color == 'r':
                                r_mercs_hp += merc.hp
                            else:
                                b_mercs_hp += merc.hp
                        
                        if r_mercs_hp != b_mercs_hp:
                            if r_mercs_hp > b_mercs_hp:
                                return "Team R is the winner!"
                            else:
                                return "Team B is the winner!"
                        else:
                            return "A winner could not be decided... Flip a coin to determine the winner!"
    else:
        return None
        # Nobody has won yet
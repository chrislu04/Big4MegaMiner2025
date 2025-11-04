# Phase 3 | Updates everything, making things move/attack and determining win/lose

from typing import List
from GameState import GameState
from UpdateMercenaries import update_mercenaries
from UpdateDemons import update_demons
from SpawnMercenaries import spawn_mercenaries
from SpawnDemons import spawn_demons
from House import House
from Cannon import Cannon
from Minigun import Minigun
from Utils import log_msg
import Constants
from Entity import Entity

def world_update_phase(game_state: GameState):
    # remove dead entities from respective lists
    game_state.mercs = [m for m in game_state.mercs if m.state != "dead"]
    game_state.demons = [d for d in game_state.demons if d.state != "dead"]

    update_mercenaries(game_state)
    mortal_wound_check(game_state, game_state.mercs + game_state.demons)
    game_state.victory = check_wincon(game_state)
    if game_state.victory != None: return

    update_demons(game_state)
    mortal_wound_check(game_state, game_state.mercs)
    game_state.victory = check_wincon(game_state)
    if game_state.victory != None: return
    
    spawn_mercenaries(game_state)
    spawn_demons(game_state)

    for tower in game_state.towers:
        tower.update(game_state)
    mortal_wound_check(game_state, game_state.mercs + game_state.demons)


def mortal_wound_check(game_state: GameState, entities: List[Entity]):
    for ent in entities:
        if ent.health <= 0 and ent.state != "dead":
            game_state.entity_grid[ent.y][ent.x] = None
            ent.state = "dead"
            log_msg(f"{ent.name} has suffered mortal wounds")


def check_wincon(game_state: GameState):
    # Determines which player wins the game, if there is an current winner
    team_b_health = game_state.player_base_b.health
    team_r_health = game_state.player_base_r.health

    team_b_money = game_state.money_b
    team_r_money = game_state.money_r

    towers = game_state.towers

    # If one of the players has had their base destroyed
    if team_b_health <= 0 or team_r_health <= 0:
        # If one of the players has their base intact while the other is destroyed, they win
        if not (team_b_health <= 0 and team_r_health <= 0):
            if team_b_health <= 0:
                log_msg("The Blue Player's base has been destroyed. The Red Nation survives!")
                return 'r'
            elif team_r_health <= 0:
                log_msg("The Red Player's base has been destroyed. The Blue Nation survives!")
                return 'b'
    else:
        # If no base has been destroyed, nobody has won yet
        return None
        
    # If both players' bases are Destroyed, break the tie based on who has the most Money.
    if team_b_money != team_r_money:
        if team_b_money > team_r_money:
            return 'b'
        elif team_r_money > team_b_money:
            return 'r'
    else:
        # Then, if both players have the same amount of Money, break the tie based on who has built the most towers.
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
                return 'r'
            else:
                return 'b'
        else:
            # Then, if both players have built the same number of towers, break the tie based on the sum of prices of those towers.
            # Equals the total price of the total amount of towers per team
            r_total_cost = 0
            b_total_cost = 0

            for tower in r_towers:
                current_team = tower.team_color

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
                else:   # Crossbow
                    if current_team == 'r':
                        r_total_cost += Constants.CROSSBOW_PRICE
                    else:
                        b_total_cost += Constants.CROSSBOW_PRICE
            if r_total_cost != b_total_cost:
                if r_total_cost > b_total_cost:
                    return 'r'
                else:
                    return 'b'
            else:
                # Then, if both sums are equal, break the tie based on the number of Mercenaries each player has.

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
                        return 'r'
                    else:
                        return 'b'
                else:
                    # Then, if both have the same number of Mercenaries, break the tie based on the sum of health of mercenaries.
                    r_mercs_health = 0
                    b_mercs_health = 0

                    for merc in game_state.mercs:
                        if merc.team_color == 'r':
                            r_mercs_health += merc.health
                        else:
                            b_mercs_health += merc.health
                    
                    if r_mercs_health != b_mercs_health:
                        if r_mercs_health > b_mercs_health:
                            return 'r'
                        else:
                            return 'b'
                    else:
                        return 'tie'
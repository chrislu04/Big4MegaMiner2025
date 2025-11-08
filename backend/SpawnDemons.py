from DemonSpawner import DemonSpawner
from Demon import Demon
from GameState import GameState
from Utils import log_msg

def spawn_demons(game_state: GameState):
    for demon_spawner in game_state.demon_spawners:
        spawner : DemonSpawner = demon_spawner
        at_target_space = game_state.entity_grid[spawner.y][spawner.x]
        
        if spawner.reload_time_left > 0:
            spawner.reload_time_left -= 1
        # Wait to spawn until space is clear
        elif at_target_space == None:
            new_demon = Demon(spawner.x, spawner.y, spawner.target_team, game_state)
            game_state.entity_grid[new_demon.y][new_demon.x] = new_demon
            game_state.demons.append(new_demon)

            spawner.reload_time_left = spawner.reload_time_max
            log_msg(f"Spawned demon {new_demon.name} at ({new_demon.x},{new_demon.y})")
        else:
            log_msg(f"Waiting to spawn demon at ({spawner.x},{spawner.y})")
    
    game_state.demon_spawner_activation_count += 1
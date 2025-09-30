from DemonSpawner import DemonSpawner
from Demon import Demon
from GameState import GameState

def spawn_demons(game_state: GameState):
    for demon_spawner in game_state.demon_spawners:
        spawner : DemonSpawner = demon_spawner
        
        if spawner.reload_time_left > 0:
            spawner.reload_time_left -= 1
        else:
            nx = spawner.x + spawner.spawn_directionX
            ny = spawner.y + spawner.spawn_directionY
            game_state.entity_grid[nx][ny] = Demon(nx, ny, spawner.target_team)
            game_state.demons.append(game_state.entity_grid[nx][ny])

            spawner.reload_time_left = spawner.reload_time_max
        
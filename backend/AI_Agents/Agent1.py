import sys
import json


## Code required to get the gamestate
if len(sys.argv) > 1:
    game_state = json.loads(sys.argv[1])

action = "build" 
coordsX = "10"
coordsY = "10"
print(action, coordsX, coordsY)
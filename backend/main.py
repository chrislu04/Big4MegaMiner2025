import sys
import subprocess
from Game import Game
from pathlib import Path

game = Game()

can_start : bool = False

## Tries to find two ai files if there is no arguments supplied
def find_files_by_pattern(pattern, search_path):
    search_path_obj = Path(search_path)
    matched_files = list(search_path_obj.rglob(pattern))
    return matched_files

default_search_dir = 'AI_Agents/'
file_pattern = "*.py"



## First check if there are no arguments supplied with the program
if len(sys.argv) <= 1: ## for python code the path to the file is an argument supplied, so there will always be 1 system arg
    files_found = find_files_by_pattern(file_pattern, default_search_dir)
    if len(files_found) >= 2 :
        print(f"Found and using files '{files_found[0]}' and '{files_found[1]}'")
        game.load_ai_paths(files_found[0], files_found[1])
        can_start = True
    else:
        print("Not enough AI Files supplied!")
    
if can_start:
    game.run()

    
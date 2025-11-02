from Game import Game
from AIAction import AIAction
import Constants
import os
import argparse
import subprocess
import sys


# Main game loop
def main_game_loop(ai_agent_1, ai_agent_2, game: Game):
    while not game.game_state.is_game_over():
        
        # Get agents' actions
        agent_1_action_string = ""
        if ai_agent_1:
            # Send game state to agent
            if game.game_state.turns_remaining < Constants.MAX_TURNS: # avoid sending initial game state twice
                ai_agent_1.stdin.write(game.game_state_to_json() + "\n--END OF TURN--\n")
                ai_agent_1.stdin.flush()
            
            # Read action from agent
            agent_1_action_string = ai_agent_1.stdout.readline().strip()
        else:
            # "Human" input from visualizer or other parent process
            agent_1_action_string = input()
        
        agent_1_action = decode_action(agent_1_action_string)

        agent_2_action_string = ""
        if ai_agent_2:
            # Send game state to agent
            if game.game_state.turns_remaining < Constants.MAX_TURNS: # avoid sending initial game state twice
                ai_agent_2.stdin.write(game.game_state_to_json() + "\n--END OF TURN--\n")
                ai_agent_2.stdin.flush()
            
            # Read action from agent
            agent_2_action_string = ai_agent_2.stdout.readline().strip()
        else:
            # "Human" input from visualizer or other parent process
            agent_2_action_string = input()
        
        agent_2_action = decode_action(agent_2_action_string)

        # Run the next turn
        game.run_turn(agent_1_action, agent_2_action)
        
        # Print a string representation of the new game state to stdout
        print(game.game_state_to_json())

        # If using the visualizer, wait for "--NEXT TURN--" from stdin
        if cmd_line_args.visualizer:
            while input() != "--NEXT TURN--":
                pass


# Use argparse to parse command line arguments
def get_command_line_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description='Backend for ApocaWarlords.',
        epilog='Example usage: python main.py <map_json_file> -a1 <ai_agent_file_1> -a2 <ai_agent_file_2>'
    )
    parser.add_argument(
        'map_json_file',
        help='Path to the map JSON file, which has tile locations, player base locations, etc.'
    )
    parser.add_argument(
        '-a1',
        '--ai_agent_file_1',
        default='backend/AI_Agents/AgentTemplate.py',
        help='Path to the AI agent 1 python file'
    )
    parser.add_argument(
        '-a2',
        '--ai_agent_file_2',
        default='backend/AI_Agents/AgentTemplate.py',
        help='Path to the AI agent 2 python file'
    )
    parser.add_argument(
        '-h1',
        '--agent_1_is_human',
        action='store_true',
        help='Pass this if agent 1 is a human player...'
    )
    parser.add_argument(
        '-h2',
        '--agent_2_is_human',
        action='store_true',
        help='Pass this if agent 2 is a human player...'
    )
    parser.add_argument(
        '-v',
        '--visualizer',
        action='store_true',
        help='Enable visualizer mode (non-headless). This argument should not be used from the command line.'
    )
    return parser.parse_args()


# Return an empty string if command line arguments are valid.
# Otherwise, return a non-empty string explaining what was wrong with the arguments.
def validate_command_line_arguments(cmd_line_args: argparse.Namespace) -> str:
    
    # Check that map file exists
    if not os.path.exists(cmd_line_args.map_json_file):
        return f'Map file not found: {cmd_line_args.map_json_file}'
    
    # Agent 1: Must have either AI agent file or be human
    if not cmd_line_args.agent_1_is_human:
        if not cmd_line_args.ai_agent_file_1:
            return 'Agent 1 must either be human (--agent_1_is_human) or have an AI agent file (-a1)'
        if not os.path.exists(cmd_line_args.ai_agent_file_1):
            return f'AI agent 1 file not found: {cmd_line_args.ai_agent_file_1}'
    
    # Agent 2: Must have either AI agent file or be human
    if not cmd_line_args.agent_2_is_human:
        if not cmd_line_args.ai_agent_file_2:
            return 'Agent 2 must either be human (--agent_2_is_human) or have an AI agent file (-a2)'
        if not os.path.exists(cmd_line_args.ai_agent_file_2):
            return f'AI agent 2 file not found: {cmd_line_args.ai_agent_file_2}'
    
    return ''


# Decodes a string into an AIAction
def decode_action(action : str) -> AIAction:
    
    action_string  : str = action.split(" ")
    ai_action : AIAction = AIAction(0,0) # Base case, this action doesn't do anything

    match action_string[0].strip().lower():
        case "build":
            ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], buy=True,) # Making a lot of bold assumptions here
        case "destroy":                                                                                     
            ai_action = AIAction(int(action_string[1]), int(action_string[2]), action_string[3], destory=True,) 
        case "queue":
            ai_action = AIAction(0, 0, queue_direction=action_string[3], queue=True,) # Queuing wouldn't need an x or y, ai would just add a direction as the params
    
    return ai_action


# Entry point for the backend
if __name__ == '__main__':

    cmd_line_args = get_command_line_arguments()
    validate_command_line_arguments(cmd_line_args)

    # Create AI agents
    ai_agent_1 = None
    if cmd_line_args.ai_agent_file_1:
        ai_agent_1 = subprocess.Popen(
            [sys.executable, cmd_line_args.ai_agent_file_1],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    ai_agent_2 = None
    if cmd_line_args.ai_agent_file_2:
        ai_agent_2 = subprocess.Popen(
            [sys.executable, cmd_line_args.ai_agent_file_2],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    # Initialize the game
    game = Game(map_json_file_path = cmd_line_args.map_json_file)

    # Send initial game state to agents, then get team names
    team_name_r = ""
    if ai_agent_1:
        ai_agent_1.stdin.write("--YOU ARE RED--\n")
        ai_agent_1.stdin.write(game.game_state_to_json() + "\n--END INITIAL GAME STATE--\n")
        team_name_r = ai_agent_1.stdout.readline().strip()
    else:
        team_name_r = "Human Player (Red)"
    
    team_name_b = ""
    if ai_agent_2:
        ai_agent_2.stdin.write("--YOU ARE BLUE--\n")
        ai_agent_2.stdin.write(game.game_state_to_json() + "\n--END INITIAL GAME STATE--\n")
        team_name_b = ai_agent_2.stdout.readline().strip()
    else:
        team_name_b = "Human Player (Blue)"

    # Send initial game state and team names to the visualizer (or other parent process)
    print("--BEGIN INITIAL GAME STATE--")
    print(game.game_state_to_json())
    print(team_name_r)
    print(team_name_b)
    print("--END INITIAL GAME STATE--")

    # Main game loop
    main_game_loop(ai_agent_1, ai_agent_2, game)

    # Clean up subprocesses
    if ai_agent_1:
        ai_agent_1.terminate()
        ai_agent_1.wait()
    if ai_agent_2:
        ai_agent_2.terminate()
        ai_agent_2.wait()
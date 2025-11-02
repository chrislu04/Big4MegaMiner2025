import sys
import json
import string
import json

# Any imports from the standard library are allowed
import random

class AIAction:
    """
    Represents one turn of actions in the game.
    
    Phase 1 - Pick ONE:
        - Build a tower: AIAction("build", x, y, tower_name)
        - Destroy a tower: AIAction("destroy", x, y)
        - Do nothing: AIAction("nothing", 0, 0)
    
    Phase 2 - Optional:
        - Buy mercenary: add merc_direction="N" (or "S", "E", "W")
    
    Examples:
        AIAction("build", 5, 3, "Cannon")
        AIAction("build", 5, 3, "Cannon", merc_direction="N")
        AIAction("destroy", 2, 4)
        AIAction("nothing", 0, 0, merc_direction="S")
    """
    
    def __init__(
        self,
        action: str,
        x: int,
        y: int,
        tower_name: str = "",
        merc_direction: str = ""
    ):
        self.action = action.lower().strip()  # "build", "destroy", or "nothing"
        self.x = x
        self.y = y
        self.tower_name = tower_name.strip()
        self.merc_direction = merc_direction.upper().strip()  # "N", "S", "E", "W", or ""
    
    def to_dict(self):
        """Convert to dictionary for saving/sending"""
        return {
            'action': self.action,
            'x': self.x,
            'y': self.y,
            'tower_name': self.tower_name,
            'merc_direction': self.merc_direction
        }
    
    def to_json(self):
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

# -- HELPER FUNCTIONS --
def is_out_of_bounds(game_state: dict, x: int, y: int) -> bool:
    return x < 0 or x >= len(game_state['FloorTiles'][0]) or y < 0 or y >= len(game_state['FloorTiles'])

# team_color should be 'r' or 'b'
def get_available_queue_directions(game_state: dict, team_color: str) -> list:
    result = []
    
    offsets = {
        (0, -1): "N",
        (0, 1): "S",
        (1, 0): "E",
        (-1, 0): "W"
    }

    for offset in offsets.keys():
        player = game_state['PlayerBaseR'] if team_color == 'r' else game_state['PlayerBaseB']
        target_x = player['x'] + offset[0]
        target_y = player['y'] + offset[1]
        if (not is_out_of_bounds(game_state, target_x, target_y) and
            game_state['FloorTiles'][target_y][target_x] == "O"):
            result.append(offsets[offset])
    
    return result
    

# -- AGENT CLASS (COMPETITORS WILL IMPLEMENT THIS) --
class Agent:
    def initialize_and_set_name(self, initial_game_state: dict, team_color: str) -> str:
        # -- YOUR CODE BEGINS HERE --
        # Competitors: Do any initialization here

        # It's essential that you keep track of which team you're on
        self.team_color = team_color

        # Return a string representing your team's name
        return "Your Team Name"
        # -- YOUR CODE ENDS HERE --
    
    # Take in a dictionary representing the game state, then output an AI Action
    def do_turn(self, game_state: dict) -> AIAction:
        # -- YOUR CODE BEGINS HERE --
        # Competitors: For your convenience, it's recommended that you use the helper functions given earlier in this file
        q_directions = get_available_queue_directions(game_state, self.team_color)

        return AIAction("nothing", 0, 0, merc_direction=random.choice(q_directions))
        # -- YOUR CODE ENDS HERE --

# -- DRIVER CODE --
# Competititors: Altering code below this line will result in disqualification!
if __name__ == '__main__':

    # figure out if we're red or blue
    team_color = 'r' if input() == "--YOU ARE RED--" else 'b'

    # get initial game state
    input_buffer = [input()]
    while input_buffer[-1] != "--END INITIAL GAME STATE--":
        input_buffer.append(input())
    game_state_init = json.loads(''.join(input_buffer[:-1]))

    # create and initialize agent, set team name
    agent = Agent()
    print(agent.initialize_and_set_name(game_state_init, team_color))

    # perform first action
    print(agent.do_turn(game_state_init).to_json())

    # loop until the game is over
    while True:
        # get this turn's state
        input_buffer = [input()]
        while input_buffer[-1] != "--END OF TURN--":
            input_buffer.append(input())
        game_state_this_turn = json.loads(''.join(input_buffer[:-1]))

        # get agent action, then send it to the game server
        print(agent.do_turn(game_state_this_turn).to_json())
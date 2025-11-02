from typing import Optional
import json

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
    
    @staticmethod
    def from_dict(data):
        """Load from dictionary"""
        return AIAction(
            data['action'],
            data['x'],
            data['y'],
            data.get('tower_name', ''),
            data.get('merc_direction', '')
        )
    
    def to_json(self):
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @staticmethod
    def from_json(json_str):
        """Load from JSON string"""
        return AIAction.from_dict(json.loads(json_str))
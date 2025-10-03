
class AIAction():
    def __init__(self, x : int, y : int, tower_to_build : str = '', buy : bool = False, destory : bool = False, queue : bool = False, queue_direction : str = ''):
        self.buy_tower_action = buy
        self.destroy_tower_action = destory
        self.queue_merc_action = queue
        self.x = x
        self.y = y
        self.tower_to_build = tower_to_build.strip() ## strip get's rid of any excess spaces
        self.queue_direction = queue_direction.strip()
    
    def __str__(self):
        action_string = ""
        support_string = ""
        if self.buy_tower_action:
            action_string = "Build"
            support_string = self.tower_to_build
        elif self.destroy_tower_action:
            action_string = "Destroy"
        elif self.queue_merc_action:
            action_string = "Buy Mercenary"
            support_string = self.queue_direction

        return f"AI Action: {action_string}, Coords: ({self.x},{self.y}), Supported Action: {support_string}"

    def change_main_action(self, buy : bool = False, destory : bool = False, queue : bool = False):
        if buy:
            self.buy_tower_action = True
            self.destroy_tower_action = False
            self.queue_merc_action = False
        elif destory:
            self.destroy_tower_action = True
            self.queue_merc_action = False
            self.buy_tower_action = False
        elif queue:
            self.queue_merc_action = True
            self.destroy_tower_action = False
            self.buy_tower_action = False


    def change_coords(self, x : int, y : int):
        self.x = x
        self.y = y

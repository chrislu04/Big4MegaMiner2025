
class AIAction():
    def __init__(self, x : int, y : int, tower_to_build : str = '', buy : bool = False, destory : bool = False, queue_direction : str = ''):
        self.buy_tower_action = buy
        self.destroy_tower_action = destory
        self.queue_merc_action = queue
        self.x = x
        self.y = y
        self.tower_to_build = tower_to_build
        self.queue_direction = queue_direction
    
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

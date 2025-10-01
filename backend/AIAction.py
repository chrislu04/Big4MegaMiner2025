
class AIAction():
    def __init__(self, x : int, y : int, support_action : str, buy : bool = False, destory : bool = False, queue : bool = False):
        self.buy_tower_action = buy
        self.destroy_tower_action = destory
        self.queue_merc_action = queue
        self.x = x
        self.y = x
        self.tower = support_action ## These are just strings? I dunno what to do bout these
        self.direction = support_action
    
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

from GameObjects import *

# BALANCE: tweaking these numbers will make or break game balance

INITIAL_MONEY: int = 3
HOUSE_MONEY_PRODUCED: int = 1
DEMON_INITIAL_HP: int = 70
DEMON_ATTACK_POWER: int = 10 # TODO: increase this over time?
MERCENARY_INITIAL_HP: int = 70
MERCENARY_ATTACK_POWER: int = 10
DEMON_SPAWNER_RELOAD_TURNS: int = 10
BUILDER_PRICES: list = [4,8,16,32,64] # BALANCE: exploration/exploitation tradeoff, don't let players snowball too quickly
MAX_BUILDERS = len(BUILDER_PRICES) + 1
PLAYER_BASE_INITIAL_HP = 200
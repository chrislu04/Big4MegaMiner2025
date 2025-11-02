import sys

def clamp(x, min_x, max_x):
    return min(max(x, min_x), max_x)

def log_msg(msg: str):
    print(msg, file=sys.stderr)
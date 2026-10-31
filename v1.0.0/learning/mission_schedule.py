"""Three exact32-game balanced schedules, shuffled independently of game RNG."""
import random
from .league_policy import schedule as roles

def schedule(block,seed=17791):
    rows=[]
    for scenario in ('2','3','4'):
        for index,row in enumerate(roles(block)):
            rows.append(dict(row,scenario_id=scenario,seed=(block*32+index)%8000))
    random.Random(seed+block).shuffle(rows);return rows

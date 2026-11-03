"""Three exact32-game balanced schedules, shuffled independently of game RNG."""
import random
from .league_policy import schedule as roles

def schedule(block,seed=17791):
    rows=[]
    for scenario in ('2','3','4'):
        for index,row in enumerate(roles(block)):
            rows.append(dict(row,scenario_id=scenario,seed=(block*32+index)%8000))
    random.Random(seed+block).shuffle(rows);return rows


def rotation_descriptor(completed,origin=0):
    """A serial collector makes the completed-game boundary an exact barrier."""
    if completed<origin:raise ValueError('rotation counter precedes origin')
    offset=completed-origin
    descriptor=dict(roles(offset//32)[offset%32])
    descriptor.update(scenario_id=('3','4','2')[(offset//10)%3],seed=offset%8000)
    return descriptor

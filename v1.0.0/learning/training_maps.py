"""Deterministic geometry augmentation, isolated from game RNG and release rules."""
import random
from engine.scenario import create_release_match
from engine.types import WorldPos

FAMILIES=('release','vertical','open-cover','vertical-open-cover')
def training_scenario(seed=0,swap=False):
    w=create_release_match(seed,swap);variant=seed%4
    if variant&2:
        rng=random.Random(seed ^ 0xC0FE)
        for row in w.terrain.cells:
            for x,tile in enumerate(row):
                if tile==2 and rng.random()<.6:row[x]=0
    if variant&1:
        w.terrain.cells.reverse()
        for collection in (w.soldiers,w.vehicles,w.squads,w.facilities):
            for u in collection.values():u.pos=WorldPos(u.pos.x_cm,w.terrain.height_cm-1-u.pos.y_cm)
    w.training_map_family=FAMILIES[variant];w.terrain.cache.clear();w.terrain.revision+=1
    return w

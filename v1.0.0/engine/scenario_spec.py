"""Serializable scenario rules, separate from terrain identity and learned weights."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import yaml

@lru_cache(maxsize=1)
def _registry():
    values=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/scenarios.yaml').read_text())
    for key,value in values.items():
        if str(key)!=value['scenario_id'] or value['mode'] not in ('conquest','elimination','capture_flag'):raise ValueError('scenario identity')
        for field in ('width_m','height_m','initial_infantry','initial_vehicles','infantry_limit','vehicle_limit','time_limit_s'):
            if type(value[field]) is not int or value[field]<=0:raise ValueError('scenario '+field)
        for field in ('credits','tickets','supply'):
            if type(value[field]) is not int or value[field]<0:raise ValueError('scenario budget')
        if value['initial_infantry']>value['infantry_limit'] or value['initial_vehicles']>value['vehicle_limit']:raise ValueError('scenario roster exceeds limit')
    return values

def specification(identity='2'):return deepcopy(_registry()[str(identity)])

def rules(world):
    # Historical worlds have no scenario field. Keep their established conquest defaults.
    return getattr(world,'scenario',_registry()['2'])

def attach(world,identity):
    world.scenario=specification(identity)
    world.scenario_id=world.scenario['scenario_id'];world.mode=world.scenario['mode']
    world.map_id=world.scenario['map_id'];world.map_version=world.scenario['map_version']
    return world

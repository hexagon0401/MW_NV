"""Validated, versioned arcade unit data."""
from pathlib import Path
from math import isfinite
import yaml
from .types import Soldier

CONFIG_DIR = Path(__file__).resolve().parents[1] / 'config'


def load_units(path=None):
    data = yaml.safe_load(Path(path or CONFIG_DIR/'units.yaml').read_text())
    if set(data) != {'INF','REC','SUP','MED','ENG'}:
        raise ValueError('unit types')
    for name, spec in data.items():
        for field in ('hp','speed_mps','detection_m','cost'):
            if not isinstance(spec[field],(int,float)) or not isfinite(spec[field]) or spec[field]<=0:
                raise ValueError(field)
        if len(spec['size_px'])!=2 or any(type(x) is not int or x<=0 for x in spec['size_px']):
            raise ValueError('size_px')
        attack = spec['attack']
        if name in ('MED','ENG'):
            if attack is not None or spec['ammo'] != 0:
                raise ValueError('noncombatant attack')
        elif not attack or any(attack[k]<=0 for k in ('range_m','interval_ms','damage')) or not 0<=attack['hit_probability']<=1:
            raise ValueError('attack')
    return data


def make_soldier(id,team,pos,type_id='INF',specs=None):
    spec = (specs or load_units())[type_id]
    return Soldier(id,team,pos,type_id=type_id,hp=spec['hp'],ammo=spec['ammo'],
                   heal_pool=spec['heal_pool'],repair_pool=spec['repair_pool'])

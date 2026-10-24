"""Validated, versioned arcade unit data."""
from pathlib import Path
from math import isfinite
import yaml
from .types import Soldier

CONFIG_DIR = Path(__file__).resolve().parents[1] / 'config'


def load_units(path=None):
    data = yaml.safe_load(Path(path or CONFIG_DIR/'units.yaml').read_text())
    if set(data) != {'INF','REC','SUP','MED','ENG','AT'}:
        raise ValueError('unit types')
    for name, spec in data.items():
        for field in ('hp','speed_mps','detection_m','cost'):
            if not isinstance(spec[field],(int,float)) or not isfinite(spec[field]) or spec[field]<=0:
                raise ValueError(field)
        if len(spec['size_px'])!=2 or any(type(x) is not int or x<=0 for x in spec['size_px']):
            raise ValueError('size_px')
        if spec['armor'] not in ('soft','light','medium','heavy','air') or spec['weapon'] not in (None,'rifle','cannon','ap','he'):raise ValueError('armor/weapon')
        if not isinstance(spec['role'],str) or not spec['role']:raise ValueError('role')
        if any(type(spec[k]) is not int or spec[k]<0 for k in ('ammo','heal_pool','repair_pool')):raise ValueError('ammunition/pools')
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


def load_vehicles(path=None):
    data=yaml.safe_load(Path(path or CONFIG_DIR/'vehicles.yaml').read_text())
    if set(data)!={'LUV','APC','IFV','HEL','TRK','MBT','SPH'}:
        raise ValueError('vehicle types')
    for spec in data.values():
        for name in ('speed_mps','fuel_max','fuel_per_100m','cost','grass_factor','hp','detection_m'):
            if not isfinite(spec[name]) or spec[name]<=0:
                raise ValueError(name)
        if spec['armor'] not in ('soft','light','medium','heavy','air'):raise ValueError('armor')
        if spec['weapon'] not in (None,'rifle','cannon','ap','he'):raise ValueError('weapon')
        if type(spec['ammo']) is not int or spec['ammo']<0:raise ValueError('ammo')
        if spec['attack'] and (any(spec['attack'][k]<=0 for k in ('range_m','interval_ms','damage')) or not 0<=spec['attack']['hit_probability']<=1):raise ValueError('attack')
        if any(type(spec[k]) is not int or spec[k]<0 for k in ('capacity','cargo_capacity')):raise ValueError('capacity')
        if bool(spec['weapon'])!=bool(spec['attack']) or bool(spec['ammo'])!=bool(spec['attack']):raise ValueError('weapon/ammo contract')
        if len(spec['size_px'])!=2 or any(type(x) is not int or x<=0 for x in spec['size_px']):raise ValueError('size_px')
        if len(spec['footprint_cm'])!=2 or any(x<=0 for x in spec['footprint_cm']):
            raise ValueError('footprint_cm')
    return data


def load_weapons():
    data=yaml.safe_load((CONFIG_DIR/'weapons.yaml').read_text())
    for weapon,table in data['multipliers'].items():
        if set(table)!={'soft','light','medium','heavy','air'} or any(not isinstance(v,(int,float)) or not isfinite(v) or v<0 for v in table.values()):raise ValueError('damage multipliers')
    if any(type(v) is not int or v<=0 for v in data['artillery'].values()):raise ValueError('artillery settings')
    return data


def catalog_document():
    return dict(version='combined-arms-1',units=load_units(),vehicles=load_vehicles(),weapons=load_weapons())

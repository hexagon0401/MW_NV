"""Deterministic arrival slots from public terrain and observed friendly traffic."""
from math import hypot
from .map import Terrain


def arrival_slot(obs,vehicle,center,parking=False):
    from .transport import FootprintTerrain
    terrain=Terrain(obs['map_width_m'],obs['map_height_m']);terrain.cells=obs['terrain']
    fp=[1000,1000] if vehicle['type_id']=='HEL' else obs['catalog']['vehicles'][vehicle['type_id']]['footprint_cm']
    footprint=FootprintTerrain(terrain,fp)
    occupied=[v for v in obs['vehicles'] if v['alive'] and v['id']!=vehicle['id']]
    goals=[(o['arg0']*100,o['arg1']*100) for o in obs.get('orders',[]) if o.get('unit')!=vehicle['id'] and o.get('op')==7 and o['status'] in ('QUEUED','RUNNING') and 'arg0' in o]
    directions=[(-1,-1),(1,-1),(1,1),(-1,1),(-1,0),(0,-1),(1,0),(0,1)]
    offset=vehicle['id']%8;directions=directions[offset:]+directions[:offset]
    hq=next((f for f in obs['facilities'] if f['kind']=='HQ' and f['owner']==obs['team']),None)
    if hq and hq['pos']['x_cm']>obs['map_width_m']*50:directions=[(-dx,dy) for dx,dy in directions]
    radii=(3600,4800,6000) if parking else (1200,2400,3200)
    for radius in radii:
        for dx,dy in directions:
            x=center['x_cm']+dx*radius;y=center['y_cm']+dy*radius
            if not footprint.passable(x,y):continue
            if any(abs(v['pos']['x_cm']-x)<(obs['catalog']['vehicles'][v['type_id']]['footprint_cm'][0]+fp[0])/2+300 and abs(v['pos']['y_cm']-y)<(obs['catalog']['vehicles'][v['type_id']]['footprint_cm'][1]+fp[1])/2+300 for v in occupied):continue
            if any(hypot(gx-x,gy-y)<1200 for gx,gy in goals):continue
            # Do not choose a slot across a river/wall relative to the objective.
            if not terrain.segment_clear((center['x_cm'],center['y_cm']),(x,y),True):continue
            return x//100,y//100
    return None

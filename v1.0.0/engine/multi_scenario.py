"""Seeded irregular mission maps; geometry and game random streams are independent."""
import random
from .state import WorldState
from .config import GameConfig
from .map import Terrain,Tile
from .types import Team,WorldPos,Facility,TeamState,Squad,Vehicle,Emplacement
from .catalog import expanded_catalog,make_soldier
from .scenario_spec import specification,attach


def create(seed=0,swap=False,scenario_id='3',geometry_attempt=0):
    config=specification(scenario_id)
    if str(scenario_id)=='2':
        from .scenario import create_release_match
        w=attach(create_release_match(seed,swap),2);w.rules_version='combined-arms-5';w.catalog_version='combined-arms-3';return w
    w=WorldState(seed,GameConfig(config['width_m'],config['height_m'],.2));attach(w,scenario_id);w.swapped=swap
    w.rules_version='combined-arms-5';w.catalog_version='combined-arms-3'
    w.unit_specs,w.vehicle_specs,w.weapon_specs=expanded_catalog();w.soldiers={};w.squads={};w.vehicles={};w.facilities={};w.bases={}
    width,height=config['width_m'],config['height_m'];w.geometry_seed=0 if geometry_attempt==8 else seed;rng=random.Random(0x7A551 if geometry_attempt==8 else seed^0x7A551^(geometry_attempt*0x171))
    # Clustered irregular woods and industrial blocks instead of a repeated grid.
    for _ in range(0 if geometry_attempt==8 else 150):
        cx=rng.randrange(60,width-60)//4;cy=rng.randrange(60,height-60)//4;rx=rng.randrange(3,12);ry=rng.randrange(3,10);forest=rng.random()<.65
        for y in range(max(0,cy-ry),min(w.terrain.rows,cy+ry+1)):
            for x in range(max(0,cx-rx),min(w.terrain.cols,cx+rx+1)):
                if forest:
                    if ((x-cx)/rx)**2+((y-cy)/ry)**2<=1+rng.uniform(-.15,.15):w.terrain.cells[y][x]=int(Tile.FOREST)
                elif abs(x-cx)<rx and abs(y-cy)<ry and not (x>cx+rx//3 and y>cy+ry//3):w.terrain.cells[y][x]=int(Tile.BUILDING_INTERIOR)
    # Three connected wide axes, with slight bends and joining vertical bypasses.
    for base_y in (height//4,height//2,height*3//4):
        bend=rng.randrange(-24,25)//4
        for x in range(w.terrain.cols):
            cy=base_y//4+(bend if width//3<x*4<width*2//3 else 0)
            for y in range(max(0,cy-3),min(w.terrain.rows,cy+4)):w.terrain.cells[y][x]=int(Tile.ROAD)
        # Fill bend junctions as traversable plazas so the axes never disconnect.
        for bx in (width//3//4,width*2//3//4):
            for x in range(bx-4,bx+5):
                for y in range(base_y//4-abs(bend)-4,base_y//4+abs(bend)+5):w.terrain.cells[y][x]=int(Tile.ROAD)
    for xm in (96,256,width//2,width-256,width-96):
        for x in range(xm//4-3,xm//4+4):
            for y in range(w.terrain.rows):w.terrain.cells[y][x]=int(Tile.ROAD)
    groups=[['INF']*5+['SUP','AT','MED'] for _ in range(6)]+[['INF']*3+['AT']*3+['ENG','MED'] for _ in range(2)]+[['REC']*6+['INF','MED'] for _ in range(2)]+[['INF']*3+['SUP']*2+['ENG']*2+['MED'] for _ in range(2)]
    kinds=['LUV','APC','APC','IFV','IFV','MBT','MBT','MBT','SPH','SPH','HEL','BH','BH','LB','LB','TRK']
    def clear(x,y,radius=20):
        for cy in range(max(0,(y-radius)//4),min(w.terrain.rows,(y+radius)//4+1)):
            for cx in range(max(0,(x-radius)//4),min(w.terrain.cols,(x+radius)//4+1)):w.terrain.cells[cy][cx]=int(Tile.GRASS)
    for team in Team:
        side=int(team)^int(swap);base=10000+int(team)*10000
        def point(x,y):return WorldPos(round((width-x if side else x)*100),round(y*100))
        hq=point(96,height/2);w.facilities[101+int(team)]=Facility(101+int(team),hq,'HQ',team);clear(hq.x_cm//100,hq.y_cm//100,40)
        for gi,roles in enumerate(groups):
            ids=[]
            for i,role in enumerate(roles):
                uid=base+gi*8+i+1;ids.append(uid);pos=point(160+(i//2)*1.5,180+gi*(height-360)/11+(i%2)*1.5);clear(pos.x_cm//100,pos.y_cm//100)
                u=make_soldier(uid,team,pos,role,w.unit_specs);u.squad_id=base+100+gi;w.soldiers[uid]=u
            w.squads[base+100+gi]=Squad(base+100+gi,team,w.soldiers[ids[0]].pos,ids)
        for i,kind in enumerate(kinds):
            pos=point(230+(i%2)*28,180+(i//2)*(height-360)/7);clear(pos.x_cm//100,pos.y_cm//100)
            u=Vehicle(base+200+i,team,pos,kind);w.vehicles[u.id]=u
            if kind=='TRK':u.cargo_supply=240
        w.teams[team]=TeamState(config['credits'],config['tickets'],config['supply'])
        if config['mode']=='capture_flag':_fortress(w,team,hq,side)
    for i in range(config['neutral_aa_count']):
        x=width//2+(-32 if i%2==0 else 32);y=height*(i+1)//(config['neutral_aa_count']+1);clear(x,y,24)
        # Short access path joins the central longitudinal road.
        for cx in range(min(x,width//2)//4,max(x,width//2)//4+1):
            for cy in range(y//4-2,y//4+3):w.terrain.cells[cy][cx]=int(Tile.ROAD)
        station=Emplacement(900000+i,None,WorldPos(x*100,y*100));w.vehicles[station.id]=station
    from collections import Counter
    w.squad_templates={g.id:[w.soldiers[i].type_id for i in g.member_ids] for g in w.squads.values()}
    w.desired_roster=dict(Counter(s.type_id for s in w.soldiers.values() if s.team==0)+Counter(v.type_id for v in w.vehicles.values() if v.team==0))
    w.terrain.revision+=1;w.terrain.cache.clear()
    if config['mode']=='capture_flag':w.flags={t:dict(owner=t,home=(w.facilities[101+t].pos.x_cm,w.facilities[101+t].pos.y_cm),status='home',carrier=None,x_cm=w.facilities[101+t].pos.x_cm,y_cm=w.facilities[101+t].pos.y_cm,progress_ms=0,return_ms=0) for t in (0,1)}
    w.emit('SCENARIO_STARTED',scenario_id=str(scenario_id),mode=config['mode'],seed=seed,swapped=swap)
    return w


def _fortress(w,team,hq,side):
    cx,cy=hq.x_cm//400,hq.y_cm//400
    left,right,top,bottom=cx-3,cx+3,cy-4,cy+4
    doors=[]
    for y in range(top,bottom+1):
        for x in range(left,right+1):w.terrain.cells[y][x]=int(Tile.WALL if x in (left,right) or y in (top,bottom) else Tile.HQ_FLOOR)
    front=left if side else right
    for y in (cy-2,cy+2):w.terrain.cells[y][front]=int(Tile.HQ_FLOOR);doors.append((front*400+200,y*400+200))
    w.bases[int(team)]=dict(rect=[left*400,top*400,(right+1)*400,(bottom+1)*400],room=[(cx-1)*400,(cy-1)*400,(cx+2)*400,(cy+2)*400],doors=doors,return_zone=[(cx-1)*400,(cy-1)*400,(cx+2)*400,(cy+2)*400])


def validate(w):
    from .transport import FootprintTerrain
    from .pathfinding import find_path
    from math import hypot
    vehicle_terrain=FootprintTerrain(w.terrain,w.vehicle_specs['MBT']['footprint_cm'])
    starts=[]
    for team in Team:
        soldiers=[s for s in w.soldiers.values() if s.team==team]
        vehicles=[v for v in w.vehicles.values() if v.team==team]
        if not all(w.terrain.passable(s.pos.x_cm,s.pos.y_cm) for s in soldiers):raise ValueError('illegal infantry spawn')
        for v in vehicles:
            if not FootprintTerrain(w.terrain,w.vehicle_specs[v.type_id]['footprint_cm']).passable(v.pos.x_cm,v.pos.y_cm):raise ValueError('illegal vehicle spawn')
        starts.append((vehicles[0].pos.x_cm,vehicles[0].pos.y_cm))
    anchors=[(w.config.map_width_m*50,int(w.config.map_height_m*100*f)) for f in (.25,.5,.75)]
    lengths=[]
    for start in starts:
        paths=[find_path(vehicle_terrain,start,target,True) for target in anchors]
        lengths.append([sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip([start,*p],[*p]))/100 for p in paths])
        for station in w.vehicles.values():
            if station.type_id=='AA_SITE':find_path(w.terrain,start,(station.pos.x_cm+400,station.pos.y_cm))
    if getattr(w,'mode',None)=='capture_flag':
        for team,base in w.bases.items():
            hq=w.facilities[101+team]
            for door in base['doors']:find_path(w.terrain,door,(hq.pos.x_cm,hq.pos.y_cm))
    ratio=max(sum(lengths[0]),sum(lengths[1]))/max(1,min(sum(lengths[0]),sum(lengths[1])))
    if ratio>1.25:raise ValueError('unbalanced main approaches')
    aa_lengths=[]
    for start in starts:
        values=[]
        for station in w.vehicles.values():
            if station.type_id=='AA_SITE':
                p=find_path(w.terrain,start,(station.pos.x_cm+400,station.pos.y_cm));values.append(sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip([start,*p],p))/100)
        aa_lengths.append(values)
    cover=[]
    for start in starts:
        cx,cy=start[0]//400,start[1]//400;cells=[w.terrain.cells[y][x] for y in range(max(0,cy-25),min(w.terrain.rows,cy+26)) for x in range(max(0,cx-25),min(w.terrain.cols,cx+26))];cover.append(sum(t in (2,3,4) for t in cells)/max(1,len(cells)))
    aa_ratio=max(map(sum,aa_lengths))/max(1,min(map(sum,aa_lengths))) if aa_lengths[0] else 1
    if aa_ratio>1.35:raise ValueError('unbalanced neutral AA approaches')
    w.terrain.cache.clear()
    return dict(neutral_aa_route_m=aa_lengths,neutral_aa_route_ratio=aa_ratio,spawn_cover_fraction=cover,valid=True,approaches=3,vehicle_width_m=16,team_route_m=lengths,route_ratio=max(sum(lengths[0]),sum(lengths[1]))/max(1,min(sum(lengths[0]),sum(lengths[1]))))


_build=create

def create(seed=0,swap=False,scenario_id='3'):
    if str(scenario_id)=='2':return _build(seed,swap,scenario_id)
    failures=[]
    for attempt in range(9):
        w=_build(seed,swap,scenario_id,geometry_attempt=attempt)
        try:report=validate(w)
        except ValueError as exc:failures.append(str(exc));continue
        w.generation=dict(report,attempt=attempt,fallback=attempt==8,failures=failures)
        if attempt==8:w.emit('GENERATION_FALLBACK',scenario_id=str(scenario_id),attempts=8)
        return w
    raise ValueError('verified fallback geometry invalid: '+str(failures[-1]))

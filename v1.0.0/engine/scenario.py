"""Symmetric Beta scenario with the specified starting roster and economy."""
from .state import WorldState
from .config import GameConfig
from .types import Team,WorldPos,Squad,Facility,Vehicle
from .catalog import make_soldier
from .logistics import debit,transfer_cargo


def create_match(seed=0,swap=False,expanded=False):
    w=WorldState(seed,GameConfig(256,256,.2));w.soldiers.clear();w.facilities.clear()
    w.swapped=swap
    w.facilities={201:Facility(201,WorldPos(12800,5600),radius_cm=1050),
                  202:Facility(202,WorldPos(12800,12800),radius_cm=1150),
                  203:Facility(203,WorldPos(12800,20000),radius_cm=1050,supply_per_minute=8)}
    for row in range(w.terrain.rows):
        for col in range(w.terrain.cols//2):
            tile=2 if w.rng.random()<.04 else 0
            if row in (31,32):tile=1
            w.terrain.cells[row][col]=w.terrain.cells[row][w.terrain.cols-1-col]=tile
    # Keep spawn pads and shared approach corridors clear.
    for row in range(20,44):
        for col in list(range(3,14))+list(range(50,61)):
            w.terrain.cells[row][col]=0
    for team in Team:
        side=int(team)^int(swap);direction=1 if side==0 else -1
        def pos(x,y):return WorldPos(x if side==0 else 25600-x,y)
        base=1000+int(team)*100
        w.facilities[101+int(team)]=Facility(101+int(team),pos(2400,12800),'HQ',team)
        roster=([['INF']*7+['SUP'],['INF']*7+['SUP'],['REC']*6,['INF']*5+['MED']] if expanded else [['INF']*5,['INF']*5,['REC']*3,['INF','INF','MED']])
        if expanded:w.teams[team].credits+=400
        soldier_id=base
        for group_index,roles in enumerate(roster):
            ids=[];gid=base+50+group_index
            for i,role in enumerate(roles):
                soldier_id+=1;ids.append(soldier_id)
                s=make_soldier(soldier_id,team,pos(2400-(i//2)*150,10000+group_index*1800+(i%2)*150),role,w.unit_specs)
                s.squad_id=gid;w.soldiers[soldier_id]=s
                debit(w,team,credits=w.unit_specs[role]['cost'],tickets=1)
            w.squads[gid]=Squad(gid,team,w.soldiers[ids[0]].pos,ids)
        for i,(kind,x,y) in enumerate([('APC',4400,12800),('HEL',3800,10400),('TRK',2400,12800)]):
            id=base+70+i;w.vehicles[id]=Vehicle(id,team,pos(x,y),kind)
            debit(w,team,credits=w.vehicle_specs[kind]['cost'])
            if kind=='TRK':transfer_cargo(w,id,120)
    w.emit('MATCH_STARTED',seed=seed,swapped=swap)
    return w


def create_release_match(seed=0,swap=False):
    from .map import Terrain
    w=create_match(seed,swap,expanded=True);w.config=GameConfig(1024,1024,.2)
    for collection in (w.soldiers,w.squads,w.vehicles,w.facilities):
        for unit in collection.values():unit.pos=WorldPos(unit.pos.x_cm*4,unit.pos.y_cm*4)
    for f in w.facilities.values():f.radius_cm*=4
    w.terrain=Terrain(1024,1024)
    for row in range(256):
        for col in range(128):
            tile=2 if w.rng.random()<.025 else 0
            if row in (127,128):tile=1
            w.terrain.cells[row][col]=w.terrain.cells[row][255-col]=tile
    for id,x,y,kind,owner in [(301,304,640,'HOSPITAL',Team.A),(302,720,640,'HOSPITAL',Team.B),
      (303,304,320,'TOWER',Team.A),(304,720,320,'TOWER',Team.B),
      (305,176,512,'GARAGE',Team.A),(306,848,512,'GARAGE',Team.B),
      (307,152,416,'HELIPAD',Team.A),(308,872,416,'HELIPAD',Team.B)]:
        w.facilities[id]=Facility(id,WorldPos(x*100,y*100),kind,owner)
    for f in w.facilities.values():
        if f.kind in ('HQ','HELIPAD','GARAGE','OBJECTIVE'):
            for row in range(max(0,f.pos.y_cm//400-5),min(256,f.pos.y_cm//400+6)):
                for col in range(max(0,f.pos.x_cm//400-5),min(256,f.pos.x_cm//400+6)):w.terrain.cells[row][col]=0
    for row in w.terrain.cells:
        for col in range(128):row[col]=row[255-col]=min(row[col],row[255-col])
    # Mirrored districts: wooded cover, side roads and courtyards; corridors stay open.
    for row in range(12,244):
        for col in range(12,128):
            if row%48 in (0,1) or col in (40,41,88,89):tile=1
            elif row%48 in range(12,23) and col%40 in range(12,23):tile=2
            elif row%48 in range(30,34) and col%40 in range(18,22):tile=4
            else:continue
            if any(abs(f.pos.x_cm//400-col)<8 and abs(f.pos.y_cm//400-row)<8 for f in w.facilities.values()):continue
            w.terrain.cells[row][col]=w.terrain.cells[row][255-col]=tile
    # Release roster is an initial grant, separate from purchase resources.
    from .types import TeamState
    w.soldiers.clear();w.squads.clear();w.vehicles.clear()
    roles=[['INF']*5+['SUP','AT','MED'] for _ in range(4)]+[['INF']*3+['AT']*3+['ENG','MED'] for _ in range(2)]+[['REC']*6+['INF','MED'],['INF']*3+['SUP']*2+['ENG']*2+['MED']]
    kinds=['LUV','APC','APC','IFV','IFV','MBT','MBT','SPH','HEL','TRK']
    for team in Team:
        side=int(team)^int(swap);base=10000+int(team)*10000
        def point(x,y):return WorldPos(x if side==0 else 102400-x,y)
        for gi,group in enumerate(roles):
            gid=base+100+gi;ids=[]
            for i,role in enumerate(group):
                uid=base+gi*8+i+1;ids.append(uid)
                soldier=make_soldier(uid,team,point(9600+(i//2)*150,26000+gi*6000+(i%2)*150),role,w.unit_specs)
                soldier.squad_id=gid;w.soldiers[uid]=soldier
            w.squads[gid]=Squad(gid,team,w.soldiers[ids[0]].pos,ids)
        for i,kind in enumerate(kinds):
            uid=base+200+i;v=Vehicle(uid,team,point(16000+(i%2)*1600,27000+(i//2)*10000),kind)
            if kind=='TRK':v.cargo_supply=240
            w.vehicles[uid]=v
        w.teams[team]=TeamState(credits=1000,tickets=32,supply=600)
    # Spawn and facility pads must fit every footprint and formation.
    for u in [*w.soldiers.values(),*w.vehicles.values(),*w.facilities.values()]:
        for row in range(max(0,u.pos.y_cm//400-4),min(256,u.pos.y_cm//400+5)):
            for col in range(max(0,u.pos.x_cm//400-4),min(256,u.pos.x_cm//400+5)):
                w.terrain.cells[row][col]=w.terrain.cells[row][255-col]=0
    w.terrain.cache.clear()
    return w

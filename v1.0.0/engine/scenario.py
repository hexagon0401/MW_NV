"""Symmetric Beta scenario with the specified starting roster and economy."""
from .state import WorldState
from .config import GameConfig
from .types import Team,WorldPos,Squad,Facility,Vehicle
from .catalog import make_soldier
from .logistics import debit,transfer_cargo


def create_match(seed=0,swap=False):
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
        roster=[['INF']*5,['INF']*5,['REC']*3,['INF','INF','MED']]
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

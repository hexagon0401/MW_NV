"""Completed-match-only spectator frames and demo export."""
import json
from pathlib import Path
from .replay import RecordingEngine,encode,decode
from .scenario import create_release_match
from .types import Team,WorldPos
from .objectives import summary


def frame(w):
    units=[]
    for collection in (w.soldiers,w.vehicles):
        for u in collection.values():
            spec=(w.unit_specs if u.id in w.soldiers else w.vehicle_specs)[u.type_id]
            units.append(dict(id=u.id,team=int(u.team),type_id=u.type_id,x_cm=u.pos.x_cm,y_cm=u.pos.y_cm,size_px=spec['size_px'],alive=getattr(u,'alive',True),carrier_id=getattr(u,'carrier_id',None)))
    return dict(tick=w.tick,units=units,scores={int(t):s.score for t,s in w.teams.items()},facilities=[dict(id=f.id,kind=f.kind,x_cm=f.pos.x_cm,y_cm=f.pos.y_cm,owner=None if f.owner is None else int(f.owner),progress_ms=f.progress_ms) for f in w.facilities.values()])


def export_view(engine,initial):
    w=engine.world
    if not getattr(w,'ended',False):raise ValueError('only completed matches may be published')
    return dict(version=1,width_m=w.config.map_width_m,height_m=w.config.map_height_m,terrain=w.terrain.cells,units=initial['units'],initial=initial,final=frame(w),events=w.events,summary=summary(w))


def demo(output):
    w=create_release_match(1)
    group=w.squads[1050]
    for i,id in enumerate(group.member_ids):w.soldiers[id].pos=WorldPos(49000-(i//2)*150,22400+(i%2)*150)
    group.pos=w.soldiers[group.member_ids[0]].pos
    e=RecordingEngine(w);initial=frame(e.world)
    e.submit(dict(cmd_id=1,team=0,op=2,unit=1050,arg0=512,arg1=224,ttl=3000))
    e.step(3000)
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(export_view(e,initial),separators=(',',':')))
    Path('data').mkdir(exist_ok=True)
    Path('data/demo.replay.json').write_text(json.dumps(e.document(),separators=(',',':')))
    return e


if __name__=='__main__':demo('viewer/public/demo.json')

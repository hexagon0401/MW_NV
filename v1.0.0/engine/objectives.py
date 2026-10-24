"""Conquest capture requires three living dismounted soldiers."""
from math import hypot
from .types import Team


def update_capture(w):
    for f in w.facilities.values():
        if f.kind != 'OBJECTIVE':
            continue
        counts={t:0 for t in Team}
        for s in w.soldiers.values():
            if s.alive and s.carrier_id is None and hypot(s.pos.x_cm-f.pos.x_cm,s.pos.y_cm-f.pos.y_cm)<=f.radius_cm:
                counts[s.team]+=1
        if all(counts.values()):
            continue
        team=next((t for t in Team if counts[t]>=3),None)
        if team is None or team==f.owner:
            f.progress_ms=0;f.capturing=None
            continue
        if f.capturing!=team:
            f.capturing=team;f.progress_ms=0
        f.progress_ms+=200
        w.emit('CAPTURE_PROGRESS',objective=f.id,team=int(team),progress_ms=f.progress_ms)
        required=20000 if f.owner is None else 15000
        if f.progress_ms>=required:
            f.progress_ms=0
            if f.owner is not None:
                f.owner=None
                w.emit('OBJECTIVE_NEUTRALIZED',objective=f.id)
            else:
                f.owner=team;f.capturing=None
                w.emit('OBJECTIVE_CAPTURED',objective=f.id,team=int(team))


def update_score(w):
    elapsed=w.tick+1
    if not hasattr(w,'ended'):
        w.ended=False;w.winner=None;w.overtime=False
    objectives=sorted((f for f in w.facilities.values() if f.kind=='OBJECTIVE'),key=lambda f:f.id)
    if elapsed%150==0 and objectives:
        hot=objectives[(1+(elapsed-1)//1500)%len(objectives)].id
        for f in objectives:
            if f.owner is not None:
                w.teams[f.owner].score+=1+int(f.id==hot)
        w.emit('SCORE_TICK',scores={int(t):s.score for t,s in w.teams.items()})
    scores={t:s.score for t,s in w.teams.items()}
    high=max(scores.values())
    leaders=[t for t in Team if scores[t]==high]
    reason=None
    if high>=100 and len(leaders)==1:
        w.winner=leaders[0];reason='SCORE_LIMIT'
    elif elapsed>=13500:
        if not w.overtime and len(leaders)==1:
            w.winner=leaders[0];reason='TIME_LIMIT'
        else:
            w.overtime=True
            if elapsed>=15000:
                w.winner=leaders[0] if len(leaders)==1 else None
                reason='OVERTIME_LIMIT'
    if reason:
        w.ended=True
        w.emit('MATCH_ENDED',winner=None if w.winner is None else int(w.winner),reason=reason)


def summary(w):
    return dict(seed=w.seed,ticks=w.tick,sim_seconds=w.tick/5,
                scores={int(t):s.score for t,s in w.teams.items()},
                winner=None if getattr(w,'winner',None) is None else int(w.winner),
                ended=getattr(w,'ended',False),checksum=w.checksum())

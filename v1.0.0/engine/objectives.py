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

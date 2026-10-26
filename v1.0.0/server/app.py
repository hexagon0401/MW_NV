"""Read-only completed matches, with optional loopback-only live routes."""
import json,re
from pathlib import Path
from fastapi import FastAPI,HTTPException,Query
from fastapi.staticfiles import StaticFiles


def create_app(store=None,live_runner=None,lifespan=None):
    root=Path(store or Path(__file__).resolve().parents[1]/'data').resolve()
    app=FastAPI(lifespan=lifespan)
    def load(id):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',id):raise HTTPException(404)
        path=root/(id+'.view.json')
        if not path.is_file() or path.is_symlink():raise HTTPException(404)
        data=json.loads(path.read_text())
        if not data.get('summary',{}).get('ended'):raise HTTPException(404)
        return data
    @app.get('/api/objectives')
    def objective_statistics(mode:str='',rules_version:str='',catalog_version:str='',map_id:str='',map_version:str='',map_family:str='',swapped:str='',policy_a:str='',policy_b:str=''):
        from learning.objective_stats import document,report
        from learning.results import records
        import sqlite3
        filters={k:v for k,v in locals().copy().items() if isinstance(v,str) and v}
        try:return report(document(records(root/'results.sqlite',kind='match')),filters)
        except (sqlite3.Error,ValueError,KeyError):raise HTTPException(503,'objective statistics unavailable')
    @app.get('/api/history')
    @app.get('/history')
    def history(offset:int=Query(0,ge=0)):
        from learning.public_results import document
        d=document(root/'results.sqlite');rows=d['matches'];return dict(total=len(rows),items=rows[offset:offset+50],next=offset+50 if offset+50<len(rows) else None,updated_at=d['updated_at'])
    @app.get('/api/training')
    @app.get('/training')
    def training():
        path=root/'training-status.json'
        if not path.is_file():path=root/'nim-approved-training'/'training-status.json'
        if not path.is_file():raise HTTPException(503,'training status unavailable')
        return json.loads(path.read_text())
    @app.get('/api/stats')
    @app.get('/stats')
    def stats():
        from learning.results import aggregate
        import sqlite3
        try:return aggregate(root/'results.sqlite')
        except (sqlite3.Error,ValueError,KeyError):raise HTTPException(503,'results unavailable')
    @app.get('/api/matches')
    @app.get('/matches')
    def matches():
        result=[]
        for path in sorted(root.glob('*.view.json')):
            id=path.name[:-10]
            try:result.append(dict(id=id,summary=load(id)['summary']))
            except HTTPException:continue
        return result
    @app.get('/api/matches/{id}')
    @app.get('/matches/{id}')
    def metadata(id:str):return dict(id=id,summary=load(id)['summary'])
    @app.get('/api/matches/{id}/view')
    @app.get('/matches/{id}/view')
    def view(id:str):return load(id)
    @app.get('/api/events')
    @app.get('/events')
    def events(match_id:str,after:int=Query(-1,ge=-1),limit:int=Query(1000,ge=1,le=10000)):
        return [e for e in load(match_id)['events'] if e['event_id']>after][:limit]
    @app.get('/api/snapshot')
    @app.get('/snapshot')
    def snapshot(match_id:str):return load(match_id)['final']
    if live_runner is not None:
        from .live import mount_live
        mount_live(app,live_runner)
    build=Path(__file__).resolve().parents[1]/'viewer'/'dist'
    if build.is_dir():app.mount('/viewer',StaticFiles(directory=build,html=True),name='viewer')
    return app


app=create_app()

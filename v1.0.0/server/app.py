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
    @app.get('/api/training')
    @app.get('/training')
    def training():
        path=root/'nim-approved-training'/'training-status.json'
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

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
    def release_registry():
        from server.releases import Registry
        folder=root/'releases'
        if not (folder/'registry.sqlite').exists():raise HTTPException(503,'release registry unavailable')
        return Registry(folder)
    @app.get('/api/releases')
    def releases():
        from server.release_observations import read
        import time
        registry=release_registry();snapshot=read(root/'releases/snapshot.json');online=time.time()-snapshot.get('last_seen',0)<45
        return dict(schema=1,items=registry.all(),updated_at=snapshot.get('updated_at'),online=online)
    @app.get('/api/releases/{id}')
    def release(id:str):
        try:return release_registry().get(id)
        except (KeyError,ValueError):raise HTTPException(404,'release not found')
    @app.get('/api/releases/{id}/events')
    def release_events(id:str,after:int|None=Query(None,ge=0),before:int|None=Query(None,ge=0)):
        if after is not None and before is not None:raise HTTPException(400,'invalid cursor')
        try:return dict(items=release_registry().events(id,after,before))
        except ValueError:raise HTTPException(400,'invalid release query')
    @app.get('/api/insights')
    def learning_insights(game_mode:str='',scenario_id:str='',learner:str='',generation:int|None=None,execution_kind:str='',evidence:str=''):
        from learning.league_metrics import document
        from learning.strategy_evidence import filter_document
        try:
            result=filter_document(document(root/'results.sqlite',game_mode or None,scenario_id or None),learner or None,generation,execution_kind or None,evidence or None)
            from learning.strategy_history import document as history_document
            result['drilldown']=history_document(root/'results.sqlite',game_mode=game_mode or None,scenario_id=scenario_id or None,learner=learner or None,generation=generation,execution_kind=execution_kind or None,evidence=evidence or None)
            return result
        except ValueError as exc:raise HTTPException(400,str(exc))
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
    def history(offset:int=Query(0,ge=0),game_mode:str='',scenario_id:str=''):
        from learning.public_results import document
        d=document(root/'results.sqlite',game_mode or None,scenario_id or None);rows=d['matches'];return dict(total=len(rows),items=rows[offset:offset+50],next=offset+50 if offset+50<len(rows) else None,updated_at=d['updated_at'])
    @app.get('/api/training')
    @app.get('/training')
    def training():
        path=root/'training-status.json'
        if not path.is_file():path=root/'nim-approved-training'/'training-status.json'
        if not path.is_file():raise HTTPException(503,'training status unavailable')
        return json.loads(path.read_text())
    @app.get('/api/stats')
    @app.get('/stats')
    def stats(game_mode:str='',scenario_id:str=''):
        from learning.results import aggregate
        import sqlite3
        try:
            if game_mode or scenario_id:
                from learning.public_results import document
                return document(root/'results.sqlite',game_mode or None,scenario_id or None)['summary']
            return aggregate(root/'results.sqlite')
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

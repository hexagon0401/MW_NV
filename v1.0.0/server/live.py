"""Loopback-only administrative spectator. AI observations remain isolated."""
import argparse,asyncio,json,time,uuid,logging,tempfile,os
from pathlib import Path
from contextlib import asynccontextmanager
from copy import deepcopy
from threading import Condition,Event,Thread
from urllib.parse import urlparse
from fastapi import HTTPException,Request
from fastapi.responses import StreamingResponse
from engine.replay import RecordingEngine
from engine.scenario import create_release_match
from engine.viewer_export import frame,export_view
from engine.types import Team
from agents.rule_hq import RuleHQ
from agents.local_hq import LocalHQ,issue_hq_round


class LiveRunner:
    def __init__(self,engine=None,seed=0,hq='rules',endpoint='http://127.0.0.1:8080/v1',model='local',output_dir=None):
        self.engine=engine if engine is not None else RecordingEngine(create_release_match(seed))
        self.output_dir=Path(output_dir) if output_dir else None;self.initial=frame(self.engine.world);self.saved=False
        self.hq=hq;self.policies={t:LocalHQ(endpoint,model) if hq=='local' else RuleHQ() for t in Team}
        self.stream_id=uuid.uuid4().hex;self.condition=Condition();self.stop_event=Event();self.thread=None
        w=self.engine.world
        self.map=dict(catalog=dict(version=w.catalog_version,units=deepcopy(w.unit_specs),vehicles=deepcopy(w.vehicle_specs),weapons=deepcopy(w.weapon_specs)),width_m=w.config.map_width_m,height_m=w.config.map_height_m,terrain=deepcopy(w.terrain.cells))
        self.seq=-1;self.last_hq_tick=None;self._publish('ended' if getattr(w,'ended',False) else 'running')

    def _publish(self,status):
        snapshot=frame(self.engine.world)
        with self.condition:
            if self.stop_event.is_set():return
            self.seq+=1;self.latest=dict(stream_id=self.stream_id,seq=self.seq,status=status,mode='live',frame=snapshot)
            self.condition.notify_all()

    def snapshot(self,include_map=False):
        with self.condition:
            value=deepcopy(self.latest)
            if include_map:value.update(deepcopy(self.map))
            return value

    def wait_after(self,seq,timeout=10):
        with self.condition:
            self.condition.wait_for(lambda:self.seq>seq or self.stop_event.is_set(),timeout)
            return deepcopy(self.latest) if self.seq>seq else None

    def advance(self):
        if self.stop_event.is_set() or getattr(self.engine.world,'ended',False):return
        w=self.engine.world
        if w.tick%150==0 and self.last_hq_tick!=w.tick:
            self.last_hq_tick=w.tick
            if self.hq=='local':
                self._publish('waiting_for_hq');issue_hq_round(self.engine,self.policies)
            else:
                observations={t:self.engine.observe(t) for t in Team}
                for t in Team:
                    for command in self.policies[t].observe_and_issue(observations[t]):self.engine.submit_for(t,command)
        if self.stop_event.is_set():return
        self.engine.step(.2)
        if getattr(w,'ended',False) and self.output_dir is not None and not self.saved:
            self._save_completed()
        self._publish('ended' if getattr(w,'ended',False) else 'running')

    def _save_completed(self):
        self.output_dir.mkdir(parents=True,exist_ok=True)
        name='live-'+self.stream_id[:12]
        documents={'.view.json':export_view(self.engine,self.initial)}
        if hasattr(self.engine,'document'):documents['.replay.json']=self.engine.document()
        for suffix,document in documents.items():
            path=self.output_dir/(name+suffix)
            if path.exists():raise FileExistsError(path.name)
            temporary=None
            try:
                with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.output_dir,suffix='.tmp',delete=False) as output:
                    temporary=Path(output.name);json.dump(document,output,separators=(',',':'))
                os.replace(temporary,path)
            finally:
                if temporary is not None:temporary.unlink(missing_ok=True)
        self.saved=True

    def _run(self):
        try:
            while not self.stop_event.is_set() and not getattr(self.engine.world,'ended',False):
                start=time.monotonic();self.advance()
                elapsed=time.monotonic()-start
                self.stop_event.wait(.2 if self.hq=='local' and elapsed>.2 else max(0,.2-elapsed))
        except Exception:
            logging.getLogger(__name__).exception('Local live simulation stopped')
            self._publish('error')

    def start(self):
        if self.thread is not None:return
        self.thread=Thread(target=self._run,name='mw-nv-live-owner',daemon=True);self.thread.start()

    def stop(self):
        if self.stop_event.is_set():return
        self.stop_event.set()
        with self.condition:
            self.seq+=1;self.latest=deepcopy(self.latest);self.latest.update(seq=self.seq,status='stopped');self.condition.notify_all()
        if self.thread is not None:self.thread.join(timeout=2)


def local_only(request):
    local={'127.0.0.1','localhost','::1'}
    if request.url.hostname not in local:raise HTTPException(403,'local spectator only')
    origin=request.headers.get('origin')
    if origin and urlparse(origin).hostname not in local:raise HTTPException(403,'local origin required')
    if request.headers.get('sec-fetch-site')=='cross-site':raise HTTPException(403,'local origin required')


async def stream(runner,request):
    snapshot=runner.snapshot(True);seq=snapshot['seq']
    yield 'retry: 1000\nid: '+runner.stream_id+':'+str(seq)+'\nevent: snapshot\ndata: '+json.dumps(snapshot,separators=(',',':'))+'\n\n'
    if snapshot['status'] in ('ended','stopped','error'):return
    while not await request.is_disconnected():
        await asyncio.sleep(.2)
        value=await asyncio.to_thread(runner.wait_after,seq,10)
        if value is None:
            yield ': heartbeat\n\n';continue
        seq=value['seq']
        yield 'id: '+runner.stream_id+':'+str(seq)+'\nevent: state\ndata: '+json.dumps(value,separators=(',',':'))+'\n\n'
        if value['status'] in ('ended','stopped','error'):return


def mount_live(app,runner):
    @app.get('/api/live/snapshot')
    @app.get('/live/snapshot')
    def snapshot(request:Request):
        local_only(request);return runner.snapshot(True)
    @app.get('/api/live/events')
    @app.get('/live/events')
    async def events(request:Request):
        local_only(request)
        return StreamingResponse(stream(runner,request),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})


def application(runner):
    from .app import create_app
    @asynccontextmanager
    async def lifespan(app):
        runner.start()
        try:yield
        finally:runner.stop()
    return create_app(store=runner.output_dir,live_runner=runner,lifespan=lifespan)


def serve(runner,port=8000,log_level='info'):
    import uvicorn
    class LocalServer(uvicorn.Server):
        def handle_exit(self,sig,frame):
            runner.stop()
            super().handle_exit(sig,frame)
    config=uvicorn.Config(application(runner),host='127.0.0.1',port=port,
        log_level=log_level,timeout_graceful_shutdown=2)
    LocalServer(config).run()


def main():
    import uvicorn
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=1);parser.add_argument('--hq',choices=['rules','local'],default='rules');parser.add_argument('--endpoint',default='http://127.0.0.1:8080/v1');parser.add_argument('--model',default='local');parser.add_argument('--port',type=int,default=8000);parser.add_argument('--output-dir',default='data');a=parser.parse_args()
    runner=LiveRunner(seed=a.seed,hq=a.hq,endpoint=a.endpoint,model=a.model,output_dir=a.output_dir)
    serve(runner,a.port)


if __name__=='__main__':main()

from types import SimpleNamespace
import pytest
from learning.objective_stats import collect,document,report
from learning.results import record_world,records
from engine.runtime import Engine
from engine.viewer_export import frame


def initial():
 return dict(tick=0,scores={0:0,1:0},units=[],facilities=[dict(id=i,kind='OBJECTIVE',owner=None) for i in (201,202,203)])

def world(events,ticks=1000):
 return SimpleNamespace(config=SimpleNamespace(tick_s=.2),tick=ticks,events=[dict(sim_tick=t,event_kind=k,payload=p) for t,k,p in events],vehicle_specs={})

def test_first_capture_survives_loss_and_recapture_and_counts_duration():
 w=world([(99,'OBJECTIVE_CAPTURED',dict(objective=202,team=0)),(199,'OBJECTIVE_NEUTRALIZED',dict(objective=202)),(299,'OBJECTIVE_CAPTURED',dict(objective=202,team=1)),(399,'OBJECTIVE_NEUTRALIZED',dict(objective=202)),(499,'OBJECTIVE_CAPTURED',dict(objective=202,team=0))])
 p=collect(w,initial())['points']['202']
 assert p['first_team']==0 and p['first_at_s']==20
 assert p['opponent_captured_after_first'] and p['opponent_first_capture_at_s']==60
 assert p['lost_after_first'] and p['first_lost_at_s']==40 and p['regained_by_first']
 assert p['hold_s']=={'A':120.,'B':20.} and p['first_stint_s']==20
 assert p['captures']=={'A':2,'B':1} and p['control_at_s']['180']==0 and p['control_at_s']['300']=='not_reached'


def test_simultaneous_points_have_no_invented_global_order_and_unclaimed_known():
 p=collect(world([(99,'OBJECTIVE_CAPTURED',dict(objective=201,team=0)),(99,'OBJECTIVE_CAPTURED',dict(objective=202,team=1))]),initial())
 assert len(p['opening'])==2 and p['points']['203']['first_team'] is None
 d=document([row('a',p)]);r=report(d)
 assert r['opening']['simultaneous']['n']==1 and r['points']['203']['uncaptured']==1


def row(id,profile=None,winner=0,mode='training'):
 return dict(kind='match',id=id,ended=True,mode=mode,rules_version='r',policies={'A':'learner','B':'base'},seed=1,scores=[100,40],winner=winner,objective_stats=profile)


def test_first_lost_win_rate_and_combinations_filters_missing_and_draws():
 p=collect(world([(49,'OBJECTIVE_CAPTURED',dict(objective=202,team=0)),(99,'OBJECTIVE_CAPTURED',dict(objective=201,team=0)),(199,'OBJECTIVE_NEUTRALIZED',dict(objective=202))]),initial())
 d=document([row('win',p),row('draw',p,None),row('legacy'),row('eval',p,1,'evaluation')]);r=report(d,{'mode':'training'})
 assert r['coverage']=={'matches':3,'recorded':2,'missing':1}
 s=r['points']['202']['first']['A'];assert s['opponent_retake_n']==0
 assert s['n']==2 and s['wins']==1 and s['draws']==1 and s['lost_n']==2 and s['lost_wins']==1
 assert r['combinations']['201+202']['A']['n']==2
 assert report(d,{'mode':'evaluation'})['points']['202']['first']['A']['losses']==1


def test_unknown_initial_state_not_guessed_and_initial_owned_excluded():
 w=world([]);assert not collect(w)['available']
 i=initial();i['tick']=100;assert not collect(w,i)['available']
 i=initial();i['facilities'][1]['owner']=0
 p=collect(world([(199,'OBJECTIVE_NEUTRALIZED',dict(objective=202)),(299,'OBJECTIVE_CAPTURED',dict(objective=202,team=1))]),i)
 assert p['points']['202']['first_team'] is None
 assert report(document([row('a',p)]))['points']['202']['initially_owned']==1


def test_recording_is_idempotent_and_does_not_change_world_hash(tmp_path):
 e=Engine();w=e.world;w.ended=True;w.winner=0;i=frame(w);before=w.checksum()
 assert record_world(tmp_path/'r.sqlite',w,'rules',{'A':'a','B':'b'},match_id='same',initial_frame=i)
 assert not record_world(tmp_path/'r.sqlite',w,'rules',{'A':'a','B':'b'},match_id='same',initial_frame=i)
 assert w.checksum()==before and len(records(tmp_path/'r.sqlite'))==1


def test_local_objective_api_and_broken_ledger(tmp_path):
 from fastapi.testclient import TestClient
 from server.app import create_app
 from learning.results import insert
 c=TestClient(create_app(tmp_path));assert c.get('/api/objectives').status_code==200
 insert(tmp_path/'results.sqlite',row('a',collect(world([]),initial())))
 d=c.get('/api/objectives?mode=training').json();assert d['coverage']['recorded']==1
 (tmp_path/'results.sqlite').write_bytes(b'corrupt');assert c.get('/api/objectives').status_code==503


def test_objective_fields_survive_portable_export_and_import(tmp_path):
 from learning.results import insert,export_records,import_records
 db=tmp_path/'first.sqlite';data=row('portable',collect(world([(99,'OBJECTIVE_CAPTURED',dict(objective=202,team=1))]),initial()),winner=1)
 insert(db,data);export_records(db,tmp_path/'r.jsonl');assert import_records(tmp_path/'second.sqlite',tmp_path/'r.jsonl')==1
 assert records(tmp_path/'second.sqlite')[0]['objective_stats']==data['objective_stats']

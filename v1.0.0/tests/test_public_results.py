import json
from learning.public_results import document
from learning.results import insert
from engine.runtime import Engine
from engine.types import Team

def test_history_includes_all_completed_modes_once_and_no_training_steps(tmp_path):
 db=tmp_path/'r.sqlite'
 for i,mode in enumerate(('training','evaluation','hybrid','rules')):
  insert(db,dict(kind='match',id=str(i),rules_version='v',policies={'A':'p','B':'q'},mode=mode,winner=i%2,scores=[100,10],seed=i,ended=True,created_at=f'2026-10-25T00:00:0{i}Z'))
 insert(db,dict(kind='training',id='steps',rules_version='v',policies={'A':'p','B':'q'},steps=64))
 d=document(db);assert len(d['matches'])==4 and d['summary']['total_matches']==4
 assert d['matches'][0]['id']=='3' and d['summary']['teams']['A']['wins']==2

def test_presentation_events_are_outside_world_hash_and_exported():
 from engine.viewer_export import frame,export_view
 e=Engine();before=e.world.checksum();e.record_presentation('HQ_DECISION',team=0,metadata={'source':'test','reasons':[]});assert e.world.checksum()==before
 initial=frame(e.world);e.submit(dict(cmd_id=1,team=0,op=2,unit=1,arg0=100,arg1=64));e.step(.2)
 assert any(x['event_kind']=='ORDER_RUNNING' for x in e.presentation_events)
 e.step(3000);doc=export_view(e,initial)
 assert any(x['event_kind']=='ORDER_RUNNING' for x in doc['events'])
 assert any(x['event_kind']=='HQ_DECISION' for x in doc['events'])

def test_history_upload_only_changes_tail_page(tmp_path,monkeypatch):
 from learning import public_results
 import cloud.supabase_storage
 monkeypatch.chdir(tmp_path);(tmp_path/'data').mkdir()
 monkeypatch.setenv('SUPABASE_URL','https://fixture');monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','fixture')
 calls=[]
 class Storage:
  bucket='test'
  def __init__(self,*args):pass
  def _request(self,path,*args):calls.append(path);return b'{}'
 monkeypatch.setattr(cloud.supabase_storage,'PrivateStorage',Storage)
 rows=[{'id':str(i)} for i in range(120)]
 monkeypatch.setattr(public_results,'document',lambda db:dict(matches=list(reversed(rows)),updated_at='time',summary={}))
 public_results.publish();calls.clear();rows.append({'id':'120'});public_results.publish()
 assert sum('results-pages/' in p for p in calls)==1
 assert any('results-index.json' in p for p in calls)

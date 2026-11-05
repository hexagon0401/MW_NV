from engine.version import RULES_VERSION
import json
import pytest
from learning.results import insert,aggregate,export_records,import_records,record_training
pytest.importorskip('fastapi');pytest.importorskip('httpx')
from fastapi.testclient import TestClient
from server.app import create_app


def match(id,winner,mode='evaluation'):
    return dict(kind='match',id=id,rules_version=RULES_VERSION,policies={'A':'p1','B':'rules'},mode=mode,seed=1,winner=winner,scores=[100,20],ended=True)


def test_wins_draws_steps_and_idempotent_import(tmp_path):
    db=tmp_path/'results.sqlite'
    for id,winner in [('one',0),('two',1),('three',None)]:assert insert(db,match(id,winner))
    assert not insert(db,match('one',0))
    record_training(db,'p1',128,run_id='learn1')
    stats=aggregate(db);assert stats['total_matches']==3
    assert stats['teams']['A']==dict(wins=1,losses=1,draws=1,games=3,win_rate=1/3)
    assert next(g for g in stats['policies'] if g['policy']=='p1')['training_steps']==128
    bundle=tmp_path/'results.jsonl';export_records(db,bundle);other=tmp_path/'other.sqlite'
    assert import_records(other,bundle)==4 and import_records(other,bundle)==0
    assert aggregate(other)==stats
    bad=match('bad',True)
    with pytest.raises(ValueError):insert(db,bad)
    bad=match('unfinished',0);bad['ended']=False
    with pytest.raises(ValueError):insert(db,bad)
    assert aggregate(db)['total_matches']==3


def test_conflicting_import_is_atomic_and_versions_separate(tmp_path):
    db=tmp_path/'results.sqlite';insert(db,match('one',0))
    bundle=tmp_path/'bad.jsonl';bundle.write_text(json.dumps(match('new',0))+'\n'+json.dumps(match('one',1)))
    with pytest.raises(ValueError):import_records(db,bundle)
    assert aggregate(db)['total_matches']==1
    newer=match('two',0);newer['rules_version']='future';insert(db,newer)
    assert len(aggregate(db)['policies'])==4


def test_stats_api_empty_and_unavailable(tmp_path):
    client=TestClient(create_app(tmp_path))
    assert client.get('/api/stats').json()['total_matches']==0
    insert(tmp_path/'results.sqlite',match('one',0))
    assert client.get('/stats').json()['teams']['A']['wins']==1
    assert client.post('/api/stats').status_code==405
    (tmp_path/'results.sqlite').write_bytes(b'broken')
    assert client.get('/api/stats').status_code==503


def test_training_run_and_frozen_checkpoint_share_actual_steps(tmp_path):
    db=tmp_path/'results.sqlite';training=match('episode',0,'training');training['policies']['A']='run-1';insert(db,training)
    evaluation=match('heldout',0);evaluation['policies']['A']='weights-hash';insert(db,evaluation)
    record_training(db,'weights-hash',64,training_run='run-1')
    ledger=aggregate(db)
    assert all(g['training_steps']==64 for g in ledger['policies'] if g['policy'] in ('run-1','weights-hash'))
    from engine.version import RULES_VERSION
    assert ledger['training']==[dict(rules_version=RULES_VERSION,policy='weights-hash',steps=64)]

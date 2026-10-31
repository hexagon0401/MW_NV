import json
from learning.diagnostic_pool import audit
from learning.diagnostic_checkpoint import dependencies


def test_parallel_audit_recovers_completed_cases_and_collects_each_once(tmp_path):
    for mode in ('2','3','4'):
        folder=tmp_path/'audit-cases'/f'{mode}-0';folder.mkdir(parents=True)
        result=dict(scenario_id=mode,seed=0,complete=True,replay_hash_verified=True)
        (folder/'result.json').write_text(json.dumps(dict(dependencies=dependencies(),result=result)))
    report=audit(tmp_path,1,None,2)
    assert report['complete'] and report['counts']=={'2':1,'3':1,'4':1} and len(report['results'])==3
    assert audit(tmp_path,1,None,2)['results']==report['results']

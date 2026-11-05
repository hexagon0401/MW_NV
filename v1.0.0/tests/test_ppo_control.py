import json,time,uuid
from server.ppo_control import initialize,apply,state

def command(s,**extra):return dict(request_id=str(uuid.uuid4()),action='pause_ppo',actor_id='82876856',instance_id=s['instance_id'],run_id='run1',expected_version=s['version'],created_at=100,expires_at=700,**extra)
def test_private_command_is_typed_idempotent_and_versioned(tmp_path):
    s=initialize(tmp_path);c=command(s);ack=apply(tmp_path,c,'run1',now=101);assert ack['status']=='accepted' and state(tmp_path)['desired']=='paused'
    assert apply(tmp_path,c,'run1',now=102)==ack
    stale=command(s);assert apply(tmp_path,stale,'run1',now=103)['reason']=='stale_version'
    tampered=dict(c,action='resume_ppo');assert apply(tmp_path,tampered,'run1',now=103)['reason']=='id_conflict'
    s=initialize(tmp_path);resume=command(s);resume['action']='resume_ppo';assert apply(tmp_path,resume,'run1',now=104)['status']=='accepted'
    assert state(tmp_path)['desired']=='running'

def test_control_rejects_shell_unknown_actor_expiry_and_new_instance(tmp_path):
    for field,value,reason in [('action','rm -rf /','invalid_command'),('actor_id','attacker','not_admin'),('instance_id',str(uuid.uuid4()),'stale_runner'),('expires_at',99,'expired')]:
        s=initialize(tmp_path);c=command(s);c[field]=value;assert apply(tmp_path,c,'run1',now=101)['reason']==reason
    s=initialize(tmp_path);c=command(s);c['path']='/bin/sh';assert apply(tmp_path,c,'run1',now=101)['reason']=='invalid_command'
    assert state(tmp_path)['version']==0

def test_pause_survives_execution_root_transition(tmp_path,monkeypatch):
    from server.ppo_control import register
    monkeypatch.setenv('MW_NV_CONTROL_ROOT',str(tmp_path/'control'))
    register(tmp_path/'legacy',tmp_path/'source','legacy',200,'old')
    s=initialize(tmp_path/'control');c=command(s);c['run_id']='old';assert apply(tmp_path/'control',c,'old',101)['status']=='accepted'
    register(tmp_path/'mission',tmp_path/'migrated','mission',192,'new')
    assert state(tmp_path/'control')['desired']=='paused'
    s=initialize(tmp_path/'control');old=command(s);old['action']='resume_ppo';old['run_id']='old'
    assert apply(tmp_path/'control',old,'new',102)['reason']=='stale_runner'

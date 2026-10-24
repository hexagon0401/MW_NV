import json
import numpy as np
from engine.runtime import Engine
from engine.scenario import create_release_match
from engine.types import WorldPos,Team
from agents.tactics import candidates,select,commands,compatible
from agents.hybrid_hq import HybridHQ
from learning.candidate_env import CandidateEnv


def test_candidates_bounded_pure_isolated_and_conflict_free():
    e=Engine(create_release_match());before=e.world.checksum();obs=e.observe(0);items=candidates(obs)
    assert 0<len(items)<=64 and all(len(c['features'])==16 for c in items)
    chosen=select(items);assert len(chosen)<=4
    for c in commands(obs,chosen):e.submit_for(0,c)
    for c in chosen:assert len(compatible([c],[x for x in chosen if x is not c]))==1
    items=candidates(e.observe(0))
    # Moving never-observed enemies cannot affect tactical analysis.
    for u in e.world.soldiers.values():
        if u.team==Team.B:u.pos=WorldPos(90000,90000)
    assert items==candidates(e.observe(0))
    other=Engine(create_release_match());assert before==other.world.checksum()


def test_hybrid_uses_ids_and_rejects_invented_or_conflicting_selections():
    obs=Engine(create_release_match()).observe(0);seen=[]
    def answer(payload):
        compact=json.loads(payload['messages'][1]['content']);seen.append(compact)
        return json.dumps({'candidate_ids':[compact['candidates'][0]['id']]})
    h=HybridHQ(transport=answer);assert len(h.observe_and_issue(obs))==1
    assert h.last_decision['source']=='llm' and len(seen[0]['candidates'])<=12 and 'units' not in seen[0]
    h.transport=lambda _:json.dumps({'candidate_ids':[999]});assert h.observe_and_issue(obs)
    assert h.last_decision['fallback_reason']=='MODEL_OR_CANDIDATE_FAILURE'
    h.transport=lambda _:json.dumps({'candidate_ids':[True]});h.observe_and_issue(obs)
    assert h.last_decision['source']=='algorithm'


def test_new_env_contract_and_sequential_reservations():
    env=CandidateEnv();observations,_=env.reset(1)
    assert all(v.shape==(1056,) and np.isfinite(v).all() for v in observations.values())
    before=env.engine.world.tick;first=env.heuristic('A')
    env.step({'A':first,'B':64});assert env.engine.world.tick==before
    assert not env.mask('A')[first]
    for _ in range(4):
        env.step({'A':64,'B':64})
    assert env.engine.world.tick>before
    _,r,_,_,info=env.step({'A':999,'B':True})
    assert info['A']['invalid_action'] and info['B']['invalid_action'] and r['A']==-r['B']


def test_old_policy_falls_back_and_friendly_artillery_is_excluded(tmp_path):
    from agents.tactics import TacticalHQ
    from engine.sensing import update_sensing
    e=Engine(create_release_match());w=e.world
    gun=next(v for v in w.vehicles.values() if v.type_id=='SPH' and v.team==0)
    gun.pos=WorldPos(30000,50000);gun.deployment='DEPLOYED'
    enemy=next(s for s in w.soldiers.values() if s.team==1);enemy.pos=WorldPos(50000,50000)
    friend=next(s for s in w.soldiers.values() if s.team==0);friend.pos=WorldPos(50000,50100)
    w.visible={Team.A:[enemy.id],Team.B:[]};w.last_seen={Team.A:{},Team.B:{}}
    assert not any(c['command']['op']==14 for c in candidates(e.observe(0)))
    old=tmp_path/'old.npz';np.savez(old,w0=np.zeros((32,32)))
    h=TacticalHQ(str(old));assert h.observe_and_issue(e.observe(0))
    assert h.last_decision['policy']=='incompatible_policy_fallback'

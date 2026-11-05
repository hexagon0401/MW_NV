import pytest
from learning.strategy_evidence import classify,filter_document
from learning.league_metrics import new_metrics,selection,opportunity
from learning.mission_resource_metrics import collect
from types import SimpleNamespace


def test_evidence_needs_independent_replication_and_ablation():
    r=dict(observations=100,novel_vs_baseline=True,successful_training_seeds=[1,2,3])
    assert classify({})=='insufficient' and classify(r)=='discovery_candidate'
    r.update(heldout_replication_complete=True,cross_side_replication=True)
    assert classify(r)=='reproduced_tactic'
    r.update(ablation_complete=True,ablation_seed_interval=dict(low=.01,high=.2))
    assert classify(r)=='effect_confirmed'


def test_selected_rounds_do_not_exceed_opportunities():
    m=new_metrics();c=dict(role='attack',analysis={},command=dict(unit=1,op=2,target=0))
    opportunity(m,'A',[c]);selection(m,'A',c,0);selection(m,'A',c,0)
    assert m['A']['selected']['attack:direct']==2 and m['A']['selected_rounds']['attack:direct']==1


def test_ammo_zero_interval_uses_authoritative_events():
    w=SimpleNamespace(tick=31,soldiers={},vehicles={},events=[dict(sim_tick=4,event_kind='ABSTRACT_ATTACK',payload=dict(unit=1,ammo=0)),dict(sim_tick=14,event_kind='UNIT_RESUPPLIED',payload=dict(unit=1,ammo=10))])
    initial=dict(tick=0,units=[dict(id=1,team=0,ammo=1,max_ammo=30,alive=True)])
    d=collect(w,initial)
    assert d['zero_ammo_unit_seconds']['0']==2 and d['resupplied_rounds']['0']==10
    assert collect(w,None)['available'] is False


def test_insight_filter_explicitly_limits_example_scope():
    d=dict(runs=[dict(learners={'PPO1':dict(recent=[dict(generation=1,execution_kind='training')]),'PPO2':dict(recent=[])})])
    out=filter_document(d,'PPO1',1,'training');assert set(out['runs'][0]['learners'])=={'PPO1'}
    assert out['detail_scope']=='recent_examples_only' and 'PPO2' in d['runs'][0]['learners']
    with pytest.raises(ValueError):filter_document(d,'foreign')


def test_full_generation_history_does_not_truncate_to_recent_examples(tmp_path):
    from learning.results import insert
    from learning.strategy_history import document,publish
    db=tmp_path/'results.sqlite'
    for i in range(130):
        insert(db,dict(rules_version='combined-arms-6',policies={'A':'one','B':'two'},scores=[1,0],steps=0,ticks=1,seed=i,id=str(i),kind='match',ended=True,mode='training',winner=0,league=dict(run='r',generation=i,assignments={'A':'PPO1','B':'PPO2'}),game_mode='elimination',scenario_id='3'))
    d=document(db,learner='PPO1',generation=0)
    assert d['games']==1 and d['wins']==1 and d['complete']
    assert document(db,learner='PPO2')['games']==130
    class Store:
        bucket='test'
        def __init__(self):self.calls=[]
        def _request(self,*args):self.calls.append(args)
    store=Store();cache={};paths=publish(store,db,cache);first=len(store.calls);publish(store,db,cache)
    assert len(store.calls)==first+1 and len(paths)==4 # three generation buckets and index

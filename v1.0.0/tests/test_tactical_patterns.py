from types import SimpleNamespace as N
from learning.tactical_patterns import detect

def event(kind,tick,**p):return dict(event_kind=kind,sim_tick=tick-1,payload=p)

def world(events,tick=500):
    return N(events=events,tick=tick,soldiers={1:N(team=0,squad_id=10)},facilities={201:N(id=201,kind='OBJECTIVE',pos=N(x_cm=0,y_cm=0),radius_cm=1000)})

initial={'tick':0,'facilities':[{'id':201,'kind':'OBJECTIVE','owner':0}]}

def test_sequences_use_participants_and_censor_incomplete_windows():
    events=[event('DISEMBARK_DONE',10,unit=1,vehicle=20),event('OBJECTIVE_CAPTURED',40,objective=201,team=0,participants=[1]),event('UNIT_REPAIRED',450,unit=20)]
    r=detect(world(events),{'A':[],'B':[]},initial)['patterns']
    assert r['unload_capture']['success']==1 and r['repair_operate']['censored']==1
    events[1]['payload']['participants']=[]
    assert detect(world(events),{'A':[],'B':[]},initial)['patterns']['unload_capture']['failed']==1

def test_early_defense_loss_is_failure_even_when_game_ends_early():
    w=world([event('OBJECTIVE_NEUTRALIZED',50,objective=201)],tick=100)
    r=detect(w,{'A':[dict(op=4,tick=10,target=201,unit=10)],'B':[]},initial)
    assert r['patterns']['defend_hold']['failed']==1 and not r['causal_claim']

def test_missing_initial_is_not_fabricated():assert not detect(world([]),{'A':[],'B':[]},None)['available']

from engine.multi_scenario import create
from engine.mission_rules import update,reset_flag
from engine.combat import damage_unit

def test_loss_tickets_once_and_timeout_ratio():
    w=create(0,scenario_id='3');initial=w.combat_tickets[0];u=next(s for s in w.soldiers.values() if s.team==0 and w.unit_specs[s.type_id]['attack'])
    cost=w.unit_specs[u.type_id]['cost'];damage_unit(w,u,u.hp);update(w);update(w)
    assert w.combat_tickets[0]==initial-cost
    w.tick=17999;update(w)
    assert w.winner==1 and w.termination_reason=='TIME_LIMIT_TICKETS'

def test_second_completed_theft_wins_not_pickup():
    w=create(0,scenario_id='4');troops=[s for s in w.soldiers.values() if s.team==0][:3];f=w.flags[1]
    for s in troops:s.pos=w.facilities[102].pos
    for _ in range(75):update(w);w.tick+=1
    assert w.teams[0].score==1 and not getattr(w,'ended',False)
    for _ in range(10):update(w);w.tick+=1
    assert w.teams[0].score==1
    reset_flag(w,f,'test_recovered')
    for _ in range(75):update(w);w.tick+=1
    assert w.teams[0].score==2 and w.winner==0 and w.termination_reason=='FLAG_CAPTURE_LIMIT'

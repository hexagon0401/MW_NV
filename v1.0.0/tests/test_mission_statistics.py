from engine.multi_scenario import create
from engine.viewer_export import frame
from engine.mode_rules import end
from learning.results import record_world,records
from learning.public_results import document
from server.app import create_app
from fastapi.testclient import TestClient


def test_completed_modes_stats_filters_and_idempotency(tmp_path):
    db=tmp_path/'results.sqlite'
    for scenario in ('3','4'):
        w=create(2,scenario_id=scenario);initial=frame(w);end(w,0,'TEST_COMPLETE')
        assert record_world(db,w,'evaluation',{'A':'ppo1','B':'ppo2'},match_id='scenario-'+scenario,initial_frame=initial)
        assert not record_world(db,w,'evaluation',{'A':'ppo1','B':'ppo2'},match_id='scenario-'+scenario,initial_frame=initial)
    rows=records(db);assert len(rows)==2
    assert all(r['initial_roster']['BH']==2 and r['scenario_setup']['tickets']==64 for r in rows)
    d=document(db,game_mode='capture_flag');assert len(d['matches'])==1 and d['summary']['teams']['A']['wins']==1
    client=TestClient(create_app(tmp_path));assert client.get('/api/stats?scenario_id=4').json()['total_matches']==1
    assert client.get('/api/history?game_mode=elimination').json()['items'][0]['scenario_id']=='3'

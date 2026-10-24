from copy import deepcopy
from agents.rule_hq import RuleHQ
from engine.runtime import Engine
from engine.scenario import create_match
from engine.headless import run_match
from engine.types import Team


def test_hq_pure_valid_and_initial_economy():
    e=Engine(create_match());before=e.world.checksum();obs=e.observe(Team.A);copy=deepcopy(obs)
    commands=RuleHQ().observe_and_issue(obs)
    assert obs==copy and e.world.checksum()==before
    assert len(commands)<=4
    for command in commands:e.submit(command)
    for t in Team:
        assert e.world.teams[t].credits==213
        assert e.world.teams[t].tickets==54
        assert e.world.teams[t].supply==180


def test_ten_rule_matches_complete():
    for seed in range(10):
        result=run_match(seed)
        assert result['ended'] and result['ticks']<=15000
        assert result['invalid_commands']==0
        assert result['attacks']>0

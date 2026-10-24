import pytest
np=pytest.importorskip("numpy")
pytest.importorskip("pettingzoo")
from pettingzoo.test import parallel_api_test
from learning.env import HQEnv


def test_parallel_api_and_fixed_observations():
    env=HQEnv();parallel_api_test(env,num_cycles=100)
    obs,_=env.reset(seed=4)
    for _ in range(100):
        assert all(o.shape==(32,) and np.isfinite(o).all() for o in obs.values())
        obs,_,done,_,_=env.step({a:int(np.flatnonzero(env.mask(a))[0]) for a in env.agents})
        if not env.agents:obs,_=env.reset(seed=5)


def test_bad_actions_do_not_crash_and_hidden_positions_do_not_change_vector():
    env=HQEnv();env.reset(seed=1);before=env.vector('A').copy()
    from engine.types import WorldPos,Team
    for s in env.engine.world.soldiers.values():
        if s.team==Team.B:s.pos=WorldPos(24000,20000)
    assert np.array_equal(before,env.vector('A'))
    _,_,_,_,info=env.step({'A':999,'B':-5})
    assert info['A']['invalid_action'] and info['B']['invalid_action']

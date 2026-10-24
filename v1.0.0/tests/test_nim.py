import json
import pytest
from agents.hybrid_hq import HybridHQ
from agents.local_hq import LocalHQ
from engine.runtime import Engine
from engine.scenario import create_release_match


def test_nim_requires_key_and_preserves_https_allowlist(monkeypatch):
    monkeypatch.delenv('NvidiaNIM',raising=False);monkeypatch.delenv('NVIDIA_API_KEY',raising=False)
    with pytest.raises(ValueError):LocalHQ('https://integrate.api.nvidia.com/v1')
    monkeypatch.setenv('NVIDIA_API_KEY','fixture-not-a-real-key')
    for endpoint in ['https://example.com/v1','https://integrate.api.nvidia.com.evil/v1','http://integrate.api.nvidia.com/v1']:
        with pytest.raises(ValueError):LocalHQ(endpoint)
    assert LocalHQ('https://integrate.api.nvidia.com/v1').api_key=='fixture-not-a-real-key'


def test_nim_candidate_validation_and_failure_recovery(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','fixture-not-a-real-key')
    obs=Engine(create_release_match()).observe(0)
    hq=HybridHQ('https://integrate.api.nvidia.com/v1',model='nvidia/nemotron-3.5-lightning-30b-a3b',transport=lambda p:json.dumps({'candidate_ids':[]}))
    assert hq.observe_and_issue(obs)==[] and hq.last_decision['source']=='llm'
    hq.transport=lambda p:'{"candidate_ids":[999999]}'
    assert hq.observe_and_issue(obs) and hq.last_decision['source']=='algorithm'
    def offline(p):raise TimeoutError()
    hq.transport=offline
    assert hq.observe_and_issue(obs) and hq.last_decision['fallback_reason']

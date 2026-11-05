"""Actual local endpoint benchmark; does not infer model speed from mocks."""
import argparse,json,time,statistics,subprocess
from pathlib import Path
from .hybrid_hq import HybridHQ
from engine.runtime import Engine
from engine.scenario import create_release_match


def benchmark(endpoint,model,count=50,server_pid=None):
    policy=HybridHQ(endpoint,model);e=Engine(create_release_match());latencies=[];valid=0
    for i in range(count):
        obs=e.observe(i%2);start=time.perf_counter();policy.observe_and_issue(obs)
        latencies.append(time.perf_counter()-start);valid+=policy.last_decision['source']=='llm';e.step(.2)
    ordered=sorted(latencies);rss=None
    if server_pid is not None:
        if server_pid<=0:raise ValueError('server PID')
        rss=int(subprocess.check_output(['ps','-o','rss=','-p',str(server_pid)],text=True).strip())/1024
    return dict(samples=count,json_valid_rate=valid/count,p50_s=statistics.median(ordered),p95_s=ordered[min(count-1,int(count*.95))],server_rss_mb=rss,tokens_per_second=None,note='tokens/s unavailable unless endpoint reports measured token usage')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--endpoint',default='http://127.0.0.1:8080/v1');p.add_argument('--model',default='local');p.add_argument('--server-pid',type=int);p.add_argument('--output',default='data/local-model-benchmark.json');a=p.parse_args();Path(a.output).write_text(json.dumps(benchmark(a.endpoint,a.model,50,a.server_pid),indent=2)+'\n')

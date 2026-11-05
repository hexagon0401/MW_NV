"""Evidence labels require explicit independent tests, not a persuasive narrative."""
LEVELS=('insufficient','observed_change','discovery_candidate','reproduced_tactic','effect_confirmed')


def classify(record):
    if not record.get('observations'):return 'insufficient'
    if not record.get('novel_vs_baseline') or len(set(record.get('successful_training_seeds',[])))<3:return 'observed_change'
    if not record.get('heldout_replication_complete'):return 'discovery_candidate'
    if not record.get('cross_side_replication'):return 'discovery_candidate'
    interval=record.get('ablation_seed_interval',{})
    if record.get('ablation_complete') and interval.get('low',0)>0:return 'effect_confirmed'
    return 'reproduced_tactic'


def filter_document(doc,learner=None,generation=None,execution_kind=None,evidence=None):
    from copy import deepcopy
    if learner not in (None,'PPO1','PPO2'):raise ValueError('invalid learner')
    if generation is not None and (not isinstance(generation,int) or generation<0):raise ValueError('invalid generation')
    if evidence not in (None,*LEVELS):raise ValueError('invalid evidence')
    if execution_kind not in (None,'training','evaluation','hybrid','rules','demonstration','failure_replay'):raise ValueError('invalid execution kind')
    result=deepcopy(doc);out=[]
    for run in result.get('runs',[]):
        if learner:run['learners']={k:v for k,v in run.get('learners',{}).items() if k==learner}
        for l in run.get('learners',{}).values():
            rows=l.get('recent',[])
            l['recent']=[r for r in rows if (generation is None or r.get('generation')==generation) and (execution_kind is None or r.get('execution_kind')==execution_kind) and (evidence is None or r.get('evidence_level','insufficient')==evidence)]
        out.append(run)
    result['runs']=out;result['detail_scope']='recent_examples_only' if any(v is not None for v in (generation,execution_kind,evidence)) else 'full_aggregates'
    result['aggregate_scope']='original_mode_and_scenario_filters';return result

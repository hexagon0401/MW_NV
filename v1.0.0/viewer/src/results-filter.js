/** Optional task filters leave legacy index/offset pagination unchanged. */
export function resultView(index,url){const mode=url.searchParams.get('game_mode'),scenario=url.searchParams.get('scenario_id');if((mode&&!['conquest','elimination','capture_flag'].includes(mode))||(scenario&&!/^[a-zA-Z0-9_-]{1,64}$/.test(scenario)))throw Error('Invalid task filter');if(!mode&&!scenario)return index;const view=index.views?.[`${mode??'*'}:${scenario??'*'}`];return {...index,...(view??{total:0,pages:[],summary:{total_matches:0,teams:{A:{wins:0,losses:0,draws:0,games:0,win_rate:0},B:{wins:0,losses:0,draws:0,games:0,win_rate:0}}}})};}
export function filterInsights(doc,url){const mode=url.searchParams.get('game_mode'),scenario=url.searchParams.get('scenario_id');if(!mode&&!scenario)return doc;return {...(doc.task_views?.[`${mode??'*'}:${scenario??'*'}`]??{schema:1,runs:[],evidence:'insufficient'}),scope:{game_mode:mode,scenario_id:scenario}};}
export function filterStrategyInsights(doc,url){
 const learner=url.searchParams.get('learner'),raw=url.searchParams.get('generation'),kind=url.searchParams.get('execution_kind'),evidence=url.searchParams.get('evidence');
 const generation=raw===null?null:Number(raw),levels=['insufficient','observed_change','discovery_candidate','reproduced_tactic','effect_confirmed'];
 if((learner&&!['PPO1','PPO2'].includes(learner))||(raw!==null&&(!Number.isSafeInteger(generation)||generation<0||raw===''))||(kind&&!['training','evaluation','hybrid','rules','demonstration','failure_replay'].includes(kind))||(evidence&&!levels.includes(evidence)))throw Error('Invalid strategy filter');
 const result=structuredClone(doc);
 result.runs=(result.runs??[]).map(run=>({...run,learners:Object.fromEntries(Object.entries(run.learners??{}).filter(([id])=>!learner||id===learner).map(([id,l])=>[id,{...l,recent:(l.recent??[]).filter(r=>(generation===null||r.generation===generation)&&(!kind||r.execution_kind===kind)&&(!evidence||r.evidence_level===evidence))}]))}));
 return {...result,detail_scope:raw!==null||kind||evidence?'recent_examples_only':'full_aggregates',aggregate_scope:'original_mode_and_scenario_filters'};
}
export function summarizeStrategyHistory(groups,url){
 const keys=['learner','execution_kind','evidence','game_mode','scenario_id'],raw=url.searchParams.get('generation'),generation=raw===null?null:Number(raw);
 const selected=groups.filter(r=>keys.every(k=>!url.searchParams.get(k)||r[k]===url.searchParams.get(k))&&(generation===null||r.generation===generation));
 const out={scope:'all_recorded_completed_learner_appearances',complete:true,games:0,wins:0,losses:0,draws:0,groups:selected};for(const r of selected)for(const k of ['games','wins','losses','draws'])out[k]+=r[k];out.win_rate=out.games?out.wins/out.games:0;return out;
}

/** Associational first-capture statistics, not a causal or policy-strength score. */
export const OBJECTIVE_FILTERS=['mode','rules_version','catalog_version','map_id','map_version','map_family','swapped','policy_a','policy_b'];
export function addStats(target,source){for(const [k,v] of Object.entries(source??{})){if(v&&typeof v==='object')addStats(target[k]??=( {}),v);else if(typeof v==='number')target[k]=(target[k]??0)+v;}return target;}
export function objectiveReport(doc,filters={}){const summary={};for(const group of doc.cohorts??[])if(Object.entries(filters).every(([k,v])=>!v||group.conditions[k]===v))addStats(summary,group.summary);return {schema:1,facets:doc.facets,objective_names:doc.objective_names,note:doc.note,updated_at:doc.updated_at??null,filters,...summary};}
export function percentage(w,n){return n?`${(100*w/n).toFixed(1)}%`:'—';}
const sum=groups=>groups.reduce((a,b)=>addStats(a,b),{});
export function pointLine(p){const s=sum(Object.values(p?.first??{}));return {...s,rate:percentage(s.wins??0,s.n??0),lostRate:percentage(s.lost_wins??0,s.lost_n??0),meanAt:s.n?(s.first_at_s_sum/s.n).toFixed(1)+'초':'—',meanHold:s.n?(s.first_stint_s_sum/s.n).toFixed(1)+'초':'—'};}
export function startObjectiveStatistics(){
 const strip=document.querySelector('.training-strip');if(!strip)return;const button=document.createElement('button');button.id='objectives-open';button.textContent='거점 선점 분석';strip.append(button);
 const dialog=document.createElement('dialog');dialog.id='objective-dialog';dialog.setAttribute('aria-labelledby','objective-title');dialog.innerHTML='<header><h2 id="objective-title">거점 선점과 승패</h2><button id="objective-close">닫기 ×</button></header><p>최초 점령은 재수복돼도 유지됩니다. 선점과 승리의 상관관계이며 인과 효과를 뜻하지 않습니다.</p><div id="objective-filters"></div><p id="objective-coverage" role="status"></p><div id="objective-content"></div>';document.body.append(dialog);
 const filters=dialog.querySelector('#objective-filters'),coverage=dialog.querySelector('#objective-coverage'),content=dialog.querySelector('#objective-content');let version=0;
 const labels={mode:'경기 종류',rules_version:'규칙',map_id:'지도',map_version:'지도 버전',map_family:'지형 변형',swapped:'진영 반전',policy_a:'A 정책',policy_b:'B 정책'};
 const el=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
 function display(d){const c=d.coverage??{};coverage.textContent=`선점 기록 ${c.recorded??0} / 선택 조건 ${c.matches??0}경기 · 과거 정보 없음 ${c.missing??0}경기`;content.replaceChildren();
  if(!c.recorded){content.append(el('p','해당 조건의 선점 정보가 아직 없습니다. 수집 시작 이후 완료 경기부터 표시합니다.'));return;}
  const table=document.createElement('table');const head=document.createElement('tr');for(const text of ['거점','선점 사례','선점 팀 최종 승률','보유 상실 뒤 승리','평균 최초 점령','최초 연속 보유'])head.append(el('th',text));table.append(head);
  for(const [id,name] of Object.entries(d.objective_names??{})){const p=d.points?.[id],s=pointLine(p),tr=document.createElement('tr');for(const text of [name,s.n??0,s.rate,`${s.lostRate} (${s.lost_n??0}건)`,s.meanAt,s.meanHold])tr.append(el('td',text));table.append(tr);
   for(const team of ['A','B']){const x=p?.first?.[team];if(!x?.n)continue;const detail=document.createElement('tr');detail.className='objective-subrow';for(const text of [`${team}팀 선점`,x.n,percentage(x.wins,x.n),`${percentage(x.lost_wins,x.lost_n)} (${x.lost_n??0}건)`,'',''])detail.append(el('td',text));table.append(detail);}
   if(s.n){const extra=document.createElement('tr'),cell=el('td',`상대가 실제 재점령한 뒤에도 승리 ${percentage(s.opponent_retake_wins??0,s.opponent_retake_n??0)} (${s.opponent_retake_n??0}건) · 재선점 ${s.regained_n??0}건 · 재선점한 팀 승률 ${percentage(s.regained_wins??0,s.regained_n??0)} · 평균 전체 보유 ${(s.hold_s_sum/s.n).toFixed(1)}초 · 종료 점수 차 ${(s.final_margin_sum/s.n).toFixed(1)}`);cell.colSpan=6;extra.append(cell);table.append(extra);const context=document.createElement('tr'),ct=el('td',`선점 당시 평균: 점수 차 ${s.score_context_n?(s.score_margin_at_first_sum/s.score_context_n).toFixed(1):'—'} · 보병 차 ${s.army_context_n?(s.infantry_margin_at_first_sum/s.army_context_n).toFixed(1):'—'}명 · 차량 차 ${s.army_context_n?(s.vehicle_margin_at_first_sum/s.army_context_n).toFixed(1):'—'}대`);ct.colSpan=6;context.append(ct);table.append(context);}
   const detail=document.createElement('tr');const td=el('td',`미점령 ${p?.uncaptured??0}경기 · 초기 소유로 선점 경쟁 제외 ${p?.initially_owned??0}경기 · 무승부 ${s.draws??0}건`);td.colSpan=6;detail.append(td);table.append(detail);
  }
  const scroll=document.createElement('div');scroll.className='objective-table';scroll.append(table);content.append(scroll,el('p','승률은 승/해당 선점 사례(무승부 포함)입니다. 여러 조건을 합치면 진영·맵·정책 차이가 섞일 수 있습니다.'));
  content.append(el('h3','여러 거점을 같은 팀이 먼저 점령한 경우'));
  const names=d.objective_names??{};for(const [key,cases] of Object.entries(d.combinations??{})){const s=sum(Object.values(cases));content.append(el('p',`${key.split('+').map(id=>names[id]??id).join(' + ')}: ${s.n}경기 · 해당 팀 승률 ${percentage(s.wins,s.n)}`));}
  content.append(el('h3','각 팀의 첫 점령 완료 장소'));for(const [id,cases] of Object.entries(d.team_first_capture??{}))for(const [team,x] of Object.entries(cases))content.append(el('p',`${team}팀 첫 점령이 ${names[id]??id}: ${x.n}경기 · 승률 ${percentage(x.wins,x.n)}`));
  content.append(el('h3','경기 전체의 첫 점령 장소'));
  for(const [id,cases] of Object.entries(d.opening??{})){if(id==='simultaneous'){content.append(el('p',`같은 tick에 여러 거점 점령 ${cases.n}경기 — 순서 우열 미부여`));continue;}const s=sum(Object.values(cases));content.append(el('p',`${names[id]??id}: ${s.n}경기 · 첫 점령 팀 승률 ${percentage(s.wins,s.n)}`));}
 }
 async function load(){const ticket=++version;coverage.textContent='집계 불러오는 중';content.replaceChildren();const query=new URLSearchParams();for(const select of filters.querySelectorAll('select'))if(select.value)query.set(select.name,select.value);
  try{const r=await fetch('/api/objectives?'+query,{cache:'no-store'});if(!r.ok)throw Error();const d=await r.json();if(ticket!==version)return;
   {filters.replaceChildren();for(const [key,label] of Object.entries(labels)){const values=d.facets?.[key]??[];if(!values.length)continue;const wrap=el('label',label),select=document.createElement('select');select.name=key;const all=el('option','전체');all.value='';select.append(all);for(const v of values){const display={training:'학습',evaluation:'평가',hybrid:'NIM 참여',rules:'규칙',true:'진영 반전',false:'기본 진영',unknown:'정보 없음',release:'기본 지형',vertical:'상하 반전','open-cover':'수목 감소','vertical-open-cover':'상하 반전·수목 감소'};const option=el('option',display[v]??v);option.title=v;option.value=v;select.append(option);}select.value=query.get(key)??'';select.onchange=load;wrap.append(select);filters.append(wrap);}}
   display(d);
  }catch{if(ticket===version)coverage.textContent='선점 통계를 불러오지 못했습니다. 잠시 후 다시 열어 주세요.';}
 }
 button.onclick=()=>{dialog.showModal();load();};dialog.querySelector('#objective-close').onclick=()=>dialog.close();dialog.addEventListener('close',()=>version++);
}

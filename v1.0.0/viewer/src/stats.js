/** Durable match results are fetched independently of simulated/replayed time. */
let latest=null;
export function stats(){return latest;}
export async function refreshStats(fetcher=fetch){try{const response=await fetcher('/api/stats');if(!response.ok)throw Error();latest=await response.json();}catch{latest=null;}const node=document.querySelector('#total-matches');if(node)node.textContent=latest?`전체 완료 ${latest.total_matches}경기 · A ${latest.teams?.A?.wins??'—'}승 / B ${latest.teams?.B?.wins??'—'}승 / 무 ${latest.teams?.A?.draws??'—'}`:'누적 —';return latest;}

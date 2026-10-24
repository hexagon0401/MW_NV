/** Durable match results are fetched independently of simulated/replayed time. */
let latest=null;
export function stats(){return latest;}
export async function refreshStats(fetcher=fetch){try{const response=await fetcher('/api/stats');if(!response.ok)throw Error();latest=await response.json();}catch{latest=null;}const node=document.querySelector('#total-matches');if(node)node.textContent=latest?`누적 ${latest.total_matches}경기`:'누적 —';return latest;}

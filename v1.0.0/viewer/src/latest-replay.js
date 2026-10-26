// Pin the downloaded timeline; a new publication only offers an explicit refresh.
export function isNewReplay(current,matches){const latest=matches.find(m=>m.id==='training-latest');return !!(current&&latest?.sha256&&current!==latest.sha256);}
export function watchLatestReplay(publication){
 if(!publication)return;const button=document.createElement('button');button.textContent='새 경기 보기';button.hidden=true;button.onclick=()=>location.reload();document.querySelector('.transport').append(button);
 const check=async()=>{if(document.hidden)return;try{const r=await fetch('/api/matches',{cache:'no-store'});if(r.ok)button.hidden=!isNewReplay(publication,await r.json());}catch{/* Keep the pinned game on network failure. */}};
 const timer=setInterval(check,60000);window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
}

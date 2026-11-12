// Commit a completed request once; preserve the user's position at commit time.
export function commitRefresh(target,staging){
 const x=window.scrollX,y=window.scrollY;
 const nodes=[...target.querySelectorAll('*')],positions=nodes.map((n,i)=>({i,key:n.getAttribute('data-scroll-key'),top:n.scrollTop,left:n.scrollLeft,tail:n.classList.contains('release-terminal')&&n.scrollHeight-n.clientHeight-n.scrollTop<32})).filter(p=>p.top||p.left);
 const expanded=new Set([...target.querySelectorAll('details[open]')].map(n=>n.querySelector('summary')?.textContent));
 const active=document.activeElement,index=nodes.indexOf(active),selection=active&&'selectionStart' in active?[active.selectionStart,active.selectionEnd]:null;
 target.replaceChildren(...staging.childNodes);
 for(const n of target.querySelectorAll('details'))if(expanded.has(n.querySelector('summary')?.textContent))n.open=true;
 const next=[...target.querySelectorAll('*')];for(const p of positions){const n=p.key?next.find(n=>n.getAttribute('data-scroll-key')===p.key):next[p.i];if(n){n.scrollTop=p.tail?n.scrollHeight:p.top;n.scrollLeft=p.left;}}
 if(index>=0&&next[index]?.tagName===active.tagName){next[index].focus({preventScroll:true});if(selection&&next[index].setSelectionRange)try{next[index].setSelectionRange(...selection);}catch{}}
 window.scrollTo(x,y);
}

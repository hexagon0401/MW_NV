export function introSpec(width){return {columns:width<=640?6:12,characters:width<=640?120:240,duration:900};}
export function startIntro(){
 let seen=false;try{seen=sessionStorage.getItem('mw-dashboard-intro')==='1';sessionStorage.setItem('mw-dashboard-intro','1');}catch{}
 if(seen||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 const spec=introSpec(innerWidth),overlay=document.createElement('div');overlay.className='intro';overlay.setAttribute('aria-hidden','true');const glyphs='01AF│┌┐└┘░▒<>:';
 for(let col=0;col<spec.columns;col++){const n=document.createElement('span');n.className='code-column';n.style.setProperty('--x',`${(col+.5)*100/spec.columns}%`);n.style.setProperty('--duration',`${650+(col%3)*70}ms`);n.style.setProperty('--delay',`${col%3*35}ms`);n.textContent=Array.from({length:20},(_,j)=>glyphs[(col*11+j*7)%glyphs.length]).join('\n');overlay.append(n);}
 document.body.append(overlay);const remove=()=>{overlay.remove();document.removeEventListener('keydown',escape);clearTimeout(timer);};const escape=e=>{if(e.key==='Escape')remove();};document.addEventListener('keydown',escape);const timer=setTimeout(remove,900);return remove;
}

/** Anchored symbols: declutter text, never displace a simulated object. */
export function placeBadges(items,camera,width,height){
 const overlaps=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
 const projected=items.map(item=>({...item,ax:item.x_cm*.12*camera.zoom+camera.x,ay:item.y_cm*.12*camera.zoom+camera.y})).filter(b=>b.ax>=12&&b.ay>=24&&b.ax<=width-12&&b.ay<=height-45).sort((a,b)=>(b.priority??0)-(a.priority??0)||String(a.id).localeCompare(String(b.id)));
 const groups=[];
 for(const b of projected){const same=groups.find(g=>!b.selected&&!g.selected&&g.team===b.team&&g.type_id===b.type_id&&Math.hypot(g.ax-b.ax,g.ay-b.ay)<24);
  if(same){same.cluster_ids??=[same.id];same.cluster_ids.push(b.id);same.count=(same.count??1)+(b.count??1);same.is_cluster=true;continue;}groups.push({...b,x:b.ax-11,y:b.ay-11,w:22,h:22});}
 const used=groups.map(b=>({x:b.x-2,y:b.y-2,w:26,h:26}));
 for(const b of groups){const text=String(b.short??b.name??b.id)+(b.is_cluster?` ×${b.cluster_ids.length}`:''),w=Math.max(28,text.length*6+7);b.label=text;
  const box={x:b.ax+14,y:b.ay-7,w,h:15};b.showLabel=box.x+w<width-8&&!used.some(a=>overlaps(a,box));if(b.showLabel)used.push(box);
 }
 return groups;
}
export function combatRegions(frame){
 const cells=new Map();
 for(const s of [...(frame.shots??[]),...(frame.impacts??[])]){if(frame.tick-s.tick>15||frame.tick<s.tick)continue;const p=s.destination??s;if(p.x_cm==null)continue;const key=`${Math.floor(p.x_cm/8000)}:${Math.floor(p.y_cm/8000)}`;const prev=cells.get(key);if(!prev||prev.tick<s.tick)cells.set(key,{...p,tick:s.tick,id:key});}
 return [...cells.values()].sort((a,b)=>b.tick-a.tick||a.id.localeCompare(b.id)).slice(0,6);
}
export function shortId(frame,u){
 if(u.is_group)return String(u.name??'').replace(' 분대','');
 const codes={HEL:'H',MBT:'T',SPH:'G',IFV:'I',APC:'P',TRK:'S',LUV:'L'};
 const n=frame.units.filter(v=>v.team===u.team&&v.type_id===u.type_id).sort((a,b)=>a.id-b.id).findIndex(v=>v.id===u.id)+1;
 return `${u.team===0?'A':'B'}-${codes[u.type_id]??'F'}${n}`;
}

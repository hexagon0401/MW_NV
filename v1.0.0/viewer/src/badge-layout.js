/** Screen-space label placement. Positions never change simulation coordinates. */
export function placeBadges(items,camera,width,height){
 const boxes=[];
 for(const item of [...items].sort((a,b)=>(b.priority??0)-(a.priority??0)||String(a.id).localeCompare(String(b.id)))){
  const ax=item.x_cm*.12*camera.zoom+camera.x,ay=item.y_cm*.12*camera.zoom+camera.y;
  if(ax< -80||ay< -80||ax>width+80||ay>height+80)continue;
  let best=null;
  for(const [dx,dy] of [0,-95,95,-190,190].flatMap(dx=>[0,-42,42,-84,84,-126,126,-168,168].map(dy=>[dx,dy]))){
   const x=Math.max(2,Math.min(width-94,ax-46+dx)),y=Math.max(2,Math.min(height-38,ay-18+dy));
   const overlap=boxes.reduce((n,b)=>n+Math.max(0,Math.min(x+92,b.x+92)-Math.max(x,b.x))*Math.max(0,Math.min(y+36,b.y+36)-Math.max(y,b.y)),0);
   const score=overlap*10+Math.abs(dx)+Math.abs(dy);if(!best||score<best.score)best={...item,x,y,ax,ay,score};
  }
  boxes.push(best);
 }
 return boxes;
}

/** Seam-aware static decoration. Coordinate hashing never consumes engine RNG. */
import {Texture,Rectangle} from 'pixi.js';
const C={ground:'#cdd3c3',grass:'#bacbaa',ink:'#55625a',forest:'#76966d',road:'#aeb9bb',water:'#87b7c5',roof:'#9d9eac'};
export function terrainAtlas(){
 const canvas=document.createElement('canvas');canvas.width=48*16*2;canvas.height=48*10*2;const ctx=canvas.getContext('2d');
 for(let type=0;type<10;type++)for(let variant=0;variant<16;variant++){
  ctx.save();ctx.scale(2,2);ctx.translate(variant*48,type*48);
  const bases=['#aeb99a','#9ca8a5','#aeb99a','#67796c','#9caaa3','#82afb4','#7198a9','#a7a18b','#a0b28c','#859685'];ctx.fillStyle=bases[type];ctx.fillRect(0,0,48,48);
  let state=variant*5939+type*7193+71;const rand=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};
  // Fine stochastic dithering replaces repeating crosses and square soil stamps.
  for(let i=0;i<180;i++){ctx.fillStyle=i%2?'rgba(240,233,191,.055)':'rgba(51,79,55,.04)';ctx.fillRect(rand()*48,rand()*48,.55+rand(),.55+rand());}
  if(type===2){for(let i=0;i<3;i++){const x=12+rand()*24,y=12+rand()*24,r=7+rand()*5;
   ctx.fillStyle='rgba(41,62,46,.19)';ctx.beginPath();ctx.ellipse(x+5,y+6,r*1.1,r*.7,.3,0,Math.PI*2);ctx.fill();
   const g=ctx.createRadialGradient(x-r*.4,y-r*.5,1,x,y,r);g.addColorStop(0,'#bbc78f');g.addColorStop(.35,'#8fa574');g.addColorStop(.7,'#657f57');g.addColorStop(1,'#405f49');
   ctx.beginPath();for(let j=0;j<12;j++){const angle=j/12*Math.PI*2,rr=r*(.83+rand()*.17);j?ctx.lineTo(x+Math.cos(angle)*rr,y+Math.sin(angle)*rr):ctx.moveTo(x+Math.cos(angle)*rr,y+Math.sin(angle)*rr);}ctx.closePath();ctx.fillStyle=g;ctx.fill();
   for(let j=0;j<8;j++){ctx.fillStyle=j%2?'rgba(217,226,166,.18)':'rgba(42,72,48,.11)';ctx.beginPath();ctx.ellipse(x+(rand()-.5)*r,y+(rand()-.5)*r,2+rand()*2,1+rand()*2,rand()*3,0,Math.PI*2);ctx.fill();}
  }}
  if(type===5||type===6){for(let i=0;i<9;i++){ctx.strokeStyle='rgba(216,232,214,.25)';ctx.lineWidth=.45;ctx.beginPath();const x=rand()*40,y=rand()*48;ctx.moveTo(x,y);ctx.quadraticCurveTo(x+4,y-1,x+9,y);ctx.stroke();}}
  if(type===7){ctx.fillStyle='#798b80';ctx.fillRect(0,0,3,48);ctx.fillRect(45,0,3,48);for(let y=3;y<48;y+=6){ctx.fillStyle='#c3bda0';ctx.fillRect(3,y,42,4);}}
  if(type===9){ctx.fillStyle='#647e6a';ctx.beginPath();ctx.ellipse(25,29,17,10,0,0,Math.PI*2);ctx.fill();ctx.fillStyle='#b9b99a';ctx.beginPath();ctx.moveTo(10,26);ctx.lineTo(19,13);ctx.lineTo(33,17);ctx.lineTo(39,30);ctx.lineTo(17,33);ctx.fill();}
  ctx.restore();
 }
 const base=Texture.from(canvas);base.source.scaleMode='linear';const frames=new Map();
 for(let type=0;type<10;type++)for(let v=0;v<16;v++)frames.set(`${type}:${v}`,new Texture({source:base.source,frame:new Rectangle(v*96,type*96,96,96),orig:new Rectangle(0,0,48,48)}));
 return {get:(type,v)=>frames.get(`${type}:${v%16}`),destroy(){for(const t of frames.values())t.destroy(false);base.destroy(true);}};
}
export function decorateChunk(g,data,col,row){
 const cells=data.terrain??[],get=(x,y)=>cells[y]?.[x]??0;
 for(let i=0;i<32;i++){const h=((col*991+row*3343+i*7919)*2654435761)>>>0,x=h%1536,y=(h>>>11)%1536;if(get(col*32+Math.floor(x/48),row*32+Math.floor(y/48))===0)g.ellipse(x,y,35+h%90,15+h%35).fill({color:i%2?0x7d906e:0xd4ccac,alpha:.035});}
 for(let y=0;y<32;y++)for(let x=0;x<32;x++){
  const gx=col*32+x,gy=row*32+y,type=get(gx,gy),px=x*48,py=y*48,hash=((gx*73856093)^(gy*19349663))>>>0;
  if(type===4){
   g.rect(px,py,48,48).fill(0xa6b2a6);for(let i=0;i<48;i+=24)g.rect(px,py+i,48,1).fill(0x99a89b);
   if(get(gx,gy-1)!==4)g.rect(px,py,48,4).fill(0xdcd9bc);
   if(get(gx-1,gy)!==4)g.rect(px,py,3,48).fill(0xc6cdb8);
   if(get(gx+1,gy)!==4)g.rect(px+44,py,4,48).fill(0x687d70);
   if(get(gx,gy+1)!==4){g.rect(px,py+40,48,8).fill(0x7c9082);for(let x=7;x<44;x+=16)g.rect(px+x,py+41,8,4).fill(0xa9c0c4);if(gx%3===0)g.rect(px+21,py+39,8,9).fill(0x54616c);}
   if(hash%7===0)g.rect(px+14,py+12,15,19).fill(0x68777e).rect(px+16,py+14,11,13).fill(0xa9bdc1).rect(px+16,py+15,11,2).fill(0xd0d8cb);
  }
  if(type===1){
   g.rect(px,py,48,48).fill(0x9ca8a5);let up=0,down=0,left=0,right=0;for(let i=1;i<=8;i++){if(up===i-1&&get(gx,gy-i)===1)up++;if(down===i-1&&get(gx,gy+i)===1)down++;if(left===i-1&&get(gx-i,gy)===1)left++;if(right===i-1&&get(gx+i,gy)===1)right++;}
   if((up===down||up===down-1)&&up<4&&left&&right)g.rect(px+5,py+23,28,2).fill(0xd8d6bc);
   if((left===right||left===right-1)&&left<4&&up&&down)g.rect(px+23,py+5,2,28).fill(0xd8d6bc);
   if(hash%29===0)g.rect(px+8,py+13,21,1).fill(0x9da9aa);
  }
  if(type===0&&((gx>15&&gx<38)||(gx>217&&gx<240))&&gy>165&&gy<224){for(let y=4;y<48;y+=8)g.rect(px,py+y,48,1).fill(0xafb69a).rect(px,py+y+2,48,1).fill(0xd2d4b9);}
  if(type===1||type===5||type===6){for(const [dx,dy,rx,ry,rw,rh] of [[0,-1,0,0,48,3],[0,1,0,45,48,3],[-1,0,0,0,3,48],[1,0,45,0,3,48]])if(get(gx+dx,gy+dy)!==type)g.rect(px+rx,py+ry,rw,rh).fill(type===1?0x879a94:type===2?0xa5b397:0xb5c9b4);}
  if(type===0&&hash%5===0){for(let i=0;i<3;i++)g.moveTo(px+11+i*5,py+31).lineTo(px+9+i*5,py+27-i%2).stroke({color:0x738660,alpha:.22,width:.6});}
  if(type===0&&hash%193===0){g.rect(px+4,py+31,32,2).fill(0x8b9881);for(let i=5;i<38;i+=8)g.rect(px+i,py+27,2,9).fill(0x8b9881);}
  if(type===0&&gy>172&&gx>68&&gx<188&&hash%37===0){for(let i=0;i<3;i++)g.rect(px+4+i*12,py+16,10,16).fill(0xa29371).rect(px+5+i*12,py+17,8,3).fill(0xc7b892).rect(px+8+i*12,py+20,2,10).fill(0x817658);}
 }
}

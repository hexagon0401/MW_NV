/** Seam-aware static decoration. Coordinate hashing never consumes engine RNG. */
import {Texture,Rectangle} from 'pixi.js';
const C={ground:'#cdd3c3',grass:'#bacbaa',ink:'#55625a',forest:'#76966d',road:'#aeb9bb',water:'#87b7c5',roof:'#9d9eac'};
export function terrainAtlas(){const canvas=document.createElement('canvas');canvas.width=24*16;canvas.height=24*10;const c=canvas.getContext('2d');const r=(color,x,y,w=1,h=1)=>{c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));};
 for(let type=0;type<10;type++)for(let v=0;v<16;v++){c.save();c.translate(v*24,type*24);let seed=v*2317+type*7919+83;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};r(['#aeb99a','#9ca8a5','#aeb99a','#67796c','#a3b09e','#82afb4','#7198a9','#a7a18b','#a0b28c','#859685'][type],0,0,24,24);
 if([0,2,8].includes(type))for(let i=0;i<30;i++)r(i%2?'#b5bda0':'#a5b092',rand()*23,rand()*23);
 if(type===2){for(let i=0;i<1;i++){const cx=12+(v%3-1),cy=10+v%2,rad=8+v%2;r('#766b48',cx-1,cy+rad-2,3,6);r('#879872',cx-5,cy+rad+3,14,2);for(let y=-rad;y<=rad;y++)for(let x=-rad;x<=rad;x++){const d=x*x+y*y;if(d>rad*rad-((x+y+v)%3))continue;const light=(x+y)/rad;const color=light<-.65?'#b1be89':light<-.05?'#8ea574':light<.65?'#6d885c':'#496b4d';r(color,cx+x,cy+y);if(d>rad*rad*.4&&(x+y)%2===0&&light>.1)r('#5d7a53',cx+x,cy+y);}for(let j=0;j<7;j++){const lx=cx-5+(j*7+v)%11,ly=cy-5+(j*3+v)%10;r(j%2?'#829b65':'#a4b57e',lx,ly,3,2);if(j%2===0)r('#b8c490',lx,ly,2,1);}r('#c3ca9b',cx-2,cy-rad+1,3,1);}}
 if(type===5||type===6){for(let i=0;i<6;i++)r(i%2?'#a2c4c0':'#779fa9',rand()*18,rand()*23,3+Math.floor(rand()*3),1);}
 if(type===7){r('#687d70',0,0,2,24);r('#687d70',22,0,2,24);for(let y=2;y<24;y+=3)r('#bcb697',2,y,20,2);}
 if(type===9){r('#5e7863',5,11,14,8);r('#b8ba98',5,8,11,7);r('#cbd0af',6,7,7,2);r('#8c9c7d',14,10,4,7);}
 c.restore();}
 const base=Texture.from(canvas);base.source.scaleMode='nearest';const frames=new Map();for(let t=0;t<10;t++)for(let v=0;v<16;v++)frames.set(`${t}:${v}`,new Texture({source:base.source,frame:new Rectangle(v*24,t*24,24,24),orig:new Rectangle(0,0,48,48)}));return {get:(t,v)=>frames.get(`${t}:${v%16}`),destroy(){for(const t of frames.values())t.destroy(false);base.destroy(true);}};}
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
  if(type===0&&gy>172&&gx>68&&gx<188&&hash%37===0){for(let i=0;i<3;i++)g.rect(px+4+i*12,py+16,10,16).fill(0xa29371).rect(px+5+i*12,py+17,8,3).fill(0xc7b892).rect(px+8+i*12,py+20,2,10).fill(0x817658);}
 }
}
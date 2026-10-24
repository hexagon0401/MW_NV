/** Seam-aware static decoration. Coordinate hashing never consumes engine RNG. */
import {Texture,Rectangle} from 'pixi.js';
const C={ground:'#cdd3c3',grass:'#bacbaa',ink:'#55625a',forest:'#76966d',road:'#aeb9bb',water:'#87b7c5',roof:'#9d9eac'};
export function terrainAtlas(){
 const canvas=document.createElement('canvas');canvas.width=48*16;canvas.height=48*10;const ctx=canvas.getContext('2d');
 const r=(c,x,y,w,h)=>{ctx.fillStyle=c;ctx.fillRect(x,y,w,h);};
 for(let type=0;type<10;type++)for(let variant=0;variant<16;variant++){
  ctx.save();ctx.translate(variant*48,type*48);
  const random=i=>((variant*3911+type*1709+i*8191)^(i*31))>>>0;
  r([C.ground,C.road,C.grass,'#636d69',C.roof,C.water,'#7199ad','#a29a82',C.grass,'#85938a'][type],0,0,48,48);
  if(type===0||type===8){
   for(let i=0;i<30;i++){const n=random(i);r(i%3?'#c0c9b5':'#d7dccb',n%46,(n>>>8)%46,1+(n%2),1);}
   if(variant===3||variant===11){r('#bbbca6',4,12,35,12);r('#c2c2ae',1,17,45,5);for(let i=0;i<8;i++)r('#aeb49f',random(i)%40+4,15+i%7,2,1);}
  }
  if(type===1){for(let i=0;i<18;i++){const n=random(i);r('#a6b0b1',n%48,(n>>>8)%48,2,1);}r('#d8d6bc',variant%2?26:5,23,16,2);if(variant%5===0){for(let y=8;y<44;y+=7)r('#c8cec4',11,y,26,3);}}
  if(type===2){
   for(let i=0;i<3;i++){const x=3+(i%2)*19+((variant*7+i*3)%7)-3,y=3+Math.floor(i/2)*20+((variant*5+i*7)%7)-3; r('#9baa8e',x+3,y+14,17,6);r('#6d715a',x+9,y+10,3,10);r('#526c4d',x+2,y+6,18,10);r('#6e8d61',x,y+3,21,11);r('#85a174',x+4,y,13,13);r('#a1b18b',x+6,y+1,6,2);r('#748f66',x+2,y+11,8,3);}

  }
  if(type===3){r('#a2aaa2',0,4,48,12);for(let x=0;x<48;x+=12){r('#c0c5b8',x,4,10,2);r('#616d65',x+10,6,2,10);}r('#7d8a7e',0,16,48,3);}
  if(type===4){
   r('#697577',3,5,44,42);r('#c9c4bb',1,2,44,42);r('#a4a0ac',3,3,40,35);r('#b6b2ba',3,3,40,4);r('#838898',3,32,40,6);for(let y=10;y<32;y+=8)r('#9595a4',5,y,36,1);r('#d5cfc0',0,0,47,2);r('#6a7880',8,6,10,9);r('#b7ced0',9,7,8,4);r('#535f68',29,17,9,7);r('#a6b2ad',30,18,7,5);r('#777e84',34,6,3,9);r('#d1cfc3',34,6,3,2);r('#d2c8b3',19,39,10,7);r('#6c7472',21,40,6,6);
  }
  if(type===5||type===6){for(let i=0;i<8;i++){const n=random(i);r(i%2?'#9bc8d0':'#b6d3d4',n%36,(n>>>8)%47,7+n%6,1);}if(variant%3===0){r('#729eac',11,18,24,1);r('#a3c9cf',16,20,15,1);}}
  if(type===7){r('#7b8886',0,0,48,48);for(let y=3;y<47;y+=6){r('#bbbba6',1,y,46,4);r('#969c8e',4,y+3,40,1);}r('#536966',0,0,3,48);r('#536966',45,0,3,48);for(let y=0;y<48;y+=12){r('#b9c4b7',0,y,3,3);r('#b9c4b7',45,y,3,3);}}
  if(type===9){r('#68786b',8,20,32,22);r('#b5beaa',5,15,31,24);r('#85977d',6,19,29,15);r('#c7cdb7',9,15,23,4);r('#6e7d6b',13,22,4,8);r('#d2cfb7',25,21,7,7);}
  ctx.restore();
 }
 const base=Texture.from(canvas);base.source.scaleMode='nearest';const frames=new Map();
 for(let type=0;type<10;type++)for(let v=0;v<16;v++)frames.set(`${type}:${v}`,new Texture({source:base.source,frame:new Rectangle(v*48,type*48,48,48)}));
 return {get:(type,v)=>frames.get(`${type}:${v%16}`),destroy(){for(const t of frames.values())t.destroy(false);base.destroy(true);}};
}
export function decorateChunk(g,data,col,row){
 const cells=data.terrain??[],get=(x,y)=>cells[y]?.[x]??0;
 for(let y=0;y<32;y++)for(let x=0;x<32;x++){
  const gx=col*32+x,gy=row*32+y,type=get(gx,gy),px=x*48,py=y*48,hash=((gx*73856093)^(gy*19349663))>>>0;
  if(type===4){
   g.rect(px,py,48,48).fill(0xa4a0ac);for(let i=0;i<48;i+=12)g.rect(px,py+i,48,1).fill(0x9896a4);
   if(get(gx,gy-1)!==4)g.rect(px,py,48,4).fill(0xd5cfc0);
   if(get(gx-1,gy)!==4)g.rect(px,py,3,48).fill(0xc6c1bc);
   if(get(gx+1,gy)!==4)g.rect(px+44,py,4,48).fill(0x727987);
   if(get(gx,gy+1)!==4){g.rect(px,py+40,48,8).fill(0x7c8490);for(let x=7;x<44;x+=16)g.rect(px+x,py+41,8,4).fill(0xa9c0c4);if(gx%3===0)g.rect(px+21,py+39,8,9).fill(0x54616c);}
   if(hash%7===0)g.rect(px+14,py+12,15,19).fill(0x68777e).rect(px+16,py+14,11,13).fill(0xa9bdc1).rect(px+16,py+15,11,2).fill(0xd0d8cb);
  }
  if(type===1){
   g.rect(px,py,48,48).fill(0xaeb9bb);let up=0,down=0,left=0,right=0;for(let i=1;i<=8;i++){if(up===i-1&&get(gx,gy-i)===1)up++;if(down===i-1&&get(gx,gy+i)===1)down++;if(left===i-1&&get(gx-i,gy)===1)left++;if(right===i-1&&get(gx+i,gy)===1)right++;}
   if((up===down||up===down-1)&&up<4&&left&&right)g.rect(px+5,py+23,28,2).fill(0xd8d6bc);
   if((left===right||left===right-1)&&left<4&&up&&down)g.rect(px+23,py+5,2,28).fill(0xd8d6bc);
   if(hash%29===0)g.rect(px+8,py+13,21,1).fill(0x9da9aa);
  }
  if(type===0&&((gx>15&&gx<38)||(gx>217&&gx<240))&&gy>165&&gy<224){for(let y=4;y<48;y+=8)g.rect(px,py+y,48,1).fill(0xafb69a).rect(px,py+y+2,48,1).fill(0xd2d4b9);}
  if(type===1||type===2||type===5||type===6){for(const [dx,dy,rx,ry,rw,rh] of [[0,-1,0,0,48,3],[0,1,0,45,48,3],[-1,0,0,0,3,48],[1,0,45,0,3,48]])if(get(gx+dx,gy+dy)!==type)g.rect(px+rx,py+ry,rw,rh).fill(type===1?0x879a94:type===2?0xa5b397:0xb5c9b4);}
  if(type===0&&hash%31===0){g.rect(px+4,py+31,32,2).fill(0x8b9881);for(let i=5;i<38;i+=8)g.rect(px+i,py+27,2,9).fill(0x8b9881);}
  if(type===0&&gy>172&&gx>68&&gx<188&&hash%9===0){for(let i=0;i<3;i++)g.rect(px+4+i*12,py+16,10,16).fill(0xa29371).rect(px+5+i*12,py+17,8,3).fill(0xc7b892).rect(px+8+i*12,py+20,2,10).fill(0x817658);}
 }
}

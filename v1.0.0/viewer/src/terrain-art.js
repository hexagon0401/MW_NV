/** Connected native-pixel terrain. Art hashing never consumes simulation RNG. */
import {Texture,Rectangle} from 'pixi.js';
const P={earth:'#b4ad8c',ground:'#b9c4a3',light:'#c5cdb0',shade:'#aebb9a',road:'#8d9791',curb:'#c0c4b4',water:'#739f9f',bank:'#9bae8e',deep:'#678d94',roof:'#93968a',wall:'#687767'};
const hash=(x,y)=>((Math.imul(x,73856093)^Math.imul(y,19349663))>>>0);
const infos=new WeakMap();
function buildings(data){if(infos.has(data))return infos.get(data);const map=new Map(),cells=data.terrain??[];for(let y=0;y<cells.length;y++)for(let x=0;x<cells[y].length;x++){if(cells[y][x]!==4||map.has(`${x}:${y}`))continue;const component=[],queue=[[x,y]],seen=new Set([`${x}:${y}`]);for(let i=0;i<queue.length;i++){const [xx,yy]=queue[i];component.push([xx,yy]);for(const [nx,ny] of [[xx-1,yy],[xx+1,yy],[xx,yy-1],[xx,yy+1]])if(cells[ny]?.[nx]===4&&!seen.has(`${nx}:${ny}`)){seen.add(`${nx}:${ny}`);queue.push([nx,ny]);}}const b={x:Math.min(...component.map(p=>p[0])),y:Math.min(...component.map(p=>p[1])),right:Math.max(...component.map(p=>p[0])),bottom:Math.max(...component.map(p=>p[1]))};for(const [xx,yy] of component)map.set(`${xx}:${yy}`,b);}infos.set(data,map);return map;}
function tree(c,x,y,size,seed){
 const oval=(color,cx,cy,rx,ry)=>{c.fillStyle=color;for(let yy=-Math.ceil(ry);yy<=ry;yy++){const half=Math.floor(rx*Math.sqrt(Math.max(0,1-yy*yy/(ry*ry))));c.fillRect(Math.round(cx-half),Math.round(cy+yy),half*2+1,1);}};
 const rad=size/2;oval('#90a07c',x+rad+4,y+rad+7,rad,rad*.65);oval('#4f6b4e',x+rad,y+rad,rad,rad*.88);oval('#718b5b',x+rad-2,y+rad-3,rad*.86,rad*.76);oval('#91a575',x+rad-5,y+rad-5,rad*.6,rad*.54);
 for(let j=0;j<4;j++){const dx=((seed>>j*3)%13-6)*rad/11,dy=((seed>>j*4)%11-5)*rad/12;oval(j%2?'#7d9663':'#a0b17e',x+rad-3+dx,y+rad-4+dy,rad*.22,rad*.16);}
}
export function terrainAtlas(){
 const canvas=document.createElement('canvas');canvas.width=24*16;canvas.height=24*10;const c=canvas.getContext('2d');
 const r=(color,x,y,w=1,h=1)=>{c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),w,h);};
 for(let type=0;type<10;type++)for(let v=0;v<16;v++){c.save();c.translate(v*24,type*24);r([P.ground,P.road,P.shade,P.wall,P.roof,P.water,P.deep,'#9d9c83',P.ground,'#8c947d'][type],0,0,24,24);
  if([0,2,8].includes(type)){r(P.ground,0,0,24,24);}
  if(type===1){r('#929c95',1,5,20,1);if(v%4===0)r('#84918b',9,15,10,1);}
  if(type===5||type===6){for(let k=0;k<3;k++)r(k===0?'#9fbab0':'#81a7a4',(v*3+k*7)%17,(k*8+v)%23,5,1);}
  if(type===3){r('#aeb4a2',0,0,24,3);for(let y=5;y<24;y+=6)r('#536651',0,y,24,1);}
  if(type===7){r('#7c8b7a',0,1,24,2);r('#7c8b7a',0,21,24,2);for(let x=0;x<24;x+=4)r('#b6b69c',x,4,3,16);}
  if(type===9){r('#697c69',5,8,16,12);r('#a5a489',4,5,14,12);r('#c0b89b',4,5,14,2);r('#7d866f',10,7,1,10);}
  c.restore();
 }
 const base=Texture.from(canvas);base.source.scaleMode='nearest';const frames=new Map();for(let t=0;t<10;t++)for(let v=0;v<16;v++)frames.set(`${t}:${v}`,new Texture({source:base.source,frame:new Rectangle(v*24,t*24,24,24),orig:new Rectangle(0,0,48,48)}));
 function tile(ctx,data,x,y,size){const cells=data.terrain??[],get=(a,b)=>cells[b]?.[a]??0,t=get(x,y),h=hash(x,y),v=h%16;ctx.drawImage(canvas,v*24,t*24,24,24,0,0,size,size);const q=size/24,rect=(color,a,b,w,hh)=>{ctx.fillStyle=color;ctx.fillRect(a*q,b*q,w*q,hh*q);};
  if(t===2&&size<=12){rect('#82966d',0,0,24,24);for(const [dx,dy,rx,ry,rw,rh] of [[0,-1,0,0,24,3],[1,0,21,0,3,24],[0,1,0,21,24,3],[-1,0,0,0,3,24]])if(get(x+dx,y+dy)!==2)rect(dx+dy<0?'#9cac7d':'#6b865f',rx,ry,rw,rh);}
  const edges=[[0,-1,0,0,24,2],[1,0,22,0,2,24],[0,1,0,22,24,2],[-1,0,0,0,2,24]];
  if(t===0&&h%17===0){rect('#b0bd9a',4+h%12,7,3,1);rect('#c9cfb1',5+h%12,6,1,1);}
  if(t===1)for(const [dx,dy,rx,ry,w,hh] of edges)if(![1,7].includes(get(x+dx,y+dy)))rect(P.curb,rx,ry,w,hh);
  if(t===5||t===6)for(const [dx,dy,rx,ry,w,hh] of edges)if(![5,6,7].includes(get(x+dx,y+dy))){rect(P.bank,rx,ry,w,hh);if(dx)rect('#c2c3a0',rx+(dx<0?0:1),ry,1,hh);}
  if(t===4){const b=buildings(data).get(`${x}:${y}`),tone=hash(b.x,b.y)%3,roof=['#aaa58e','#8d9c92','#9a9b8d'][tone];rect(roof,0,0,24,24);if(y===b.y)rect('#c5c4aa',0,0,24,3);if(x===b.x)rect('#b9bda3',0,0,2,24);if(x===b.right)rect('#6d7d71',21,0,3,24);if(y===b.bottom){rect('#69786b',0,19,24,5);if(x%2===0)rect('#9eb5b1',7,20,8,2);}if((x-b.x)%3===1&&(y-b.y)%3===1){rect('#65776e',6,6,10,8);rect('#afbbb0',7,6,8,2);}if((y-b.y)%2===0)rect('#889584',2,12,20,1);}
  // Farm rows and soil patches are district-specific; never alter terrain collision.
  if(t===0&&y>12&&y<70&&((x>70&&x<108)||(x>148&&x<186))){for(let i=5;i<24;i+=7){rect('#a7b38c',0,i,24,1);rect('#c7c5a3',0,i+1,24,1);}}
  if(t===0&&y>175&&h%41===0){rect('#a9a482',7,7,10,8);rect('#c4bc9c',7,7,10,2);}
 }
 function trees(ctx,data,startX,startY,cols,rows,size){for(let y=startY-1;y<=startY+rows;y++)for(let x=startX-1;x<=startX+cols;x++){const h=hash(x,y);if(data.terrain?.[y]?.[x]!==2||h%5===0)continue;const q=size/24;ctx.save();ctx.translate((x-startX)*size,(y-startY)*size);ctx.scale(q,q);tree(ctx,-8+(h%13),-10+((h>>>8)%13),27+(h>>>16)%15,h);ctx.restore();}}
 function drawChunk(data,col,row,low){const out=document.createElement('canvas'),size=low?12:24;out.width=out.height=32*size;const ctx=out.getContext('2d');ctx.imageSmoothingEnabled=low;for(let y=0;y<32;y++)for(let x=0;x<32;x++){ctx.save();ctx.translate(x*size,y*size);tile(ctx,data,col*32+x,row*32+y,size);ctx.restore();}if(!low)trees(ctx,data,col*32,row*32,32,32,size);return out;}
 function overview(data){const out=document.createElement('canvas'),cells=data.terrain??[];out.width=(cells[0]?.length??256)*4;out.height=(cells.length||256)*4;const ctx=out.getContext('2d');ctx.imageSmoothingEnabled=true;for(let y=0;y<cells.length;y++)for(let x=0;x<cells[y].length;x++){ctx.save();ctx.translate(x*4,y*4);tile(ctx,data,x,y,4);ctx.restore();}return out;}
 return {get:(t,v)=>frames.get(`${t}:${v%16}`),drawChunk,overview,destroy(){for(const t of frames.values())t.destroy(false);base.destroy(true);}};
}
export function decorateChunk(){} // Legacy imports remain compatible; detail is baked into connected tiles.

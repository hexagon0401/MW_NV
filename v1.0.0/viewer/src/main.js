import {Application,Container,Graphics} from 'pixi.js';
import './style.css';
import {visibleChunks} from './viewport.js';
const host=document.querySelector('#field');
const app=new Application();await app.init({resizeTo:host,background:0x172c26,antialias:false});host.appendChild(app.canvas);
const world=new Container();app.stage.addChild(world);world.scale.set(.6);world.position.set(20,20);
const chunks=new Map();const colors=[0x314a32,0x6b6d57,0x213d2b,0x78817c,0x616b61,0x365d67,0x243f55,0x9b9069,0x616d39,0x566455];
let data;try{const response=await fetch('/demo.json');if(!response.ok)throw Error();data=await response.json();}catch{data={width_m:1024,height_m:1024,units:[],terrain:[]};}
for(let row=0;row<Math.ceil(data.height_m/128);row++)for(let col=0;col<Math.ceil(data.width_m/128);col++){
 const g=new Graphics();g.position.set(col*384,row*384);
 for(let ty=0;ty<32;ty++)for(let tx=0;tx<32;tx++){const tile=data.terrain[row*32+ty]?.[col*32+tx]??0;g.rect(tx*12,ty*12,12,12).fill(colors[tile]);}
 chunks.set(`${col},${row}`,g);world.addChild(g);
}
for(const u of data.units){const g=new Graphics();const size=u.size_px??[3,5];g.rect(-size[0]/2,-size[1]/2,...size).fill(u.team===0?0x6ec1ec:0xf28275);g.position.set(u.x_cm*.03,u.y_cm*.03);world.addChild(g);}
let drag;host.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY};host.setPointerCapture(e.pointerId);});host.addEventListener('pointerup',()=>drag=null);host.addEventListener('pointermove',e=>{if(!drag)return;world.x+=e.clientX-drag.x;world.y+=e.clientY-drag.y;drag={x:e.clientX,y:e.clientY};});
host.addEventListener('wheel',e=>{e.preventDefault();const box=host.getBoundingClientRect(),x=e.clientX-box.left,y=e.clientY-box.top;const old=world.scale.x,next=Math.min(8,Math.max(.15,old*Math.exp(-e.deltaY*.001)));world.x=x-(x-world.x)*next/old;world.y=y-(y-world.y)*next/old;world.scale.set(next);},{passive:false});
app.ticker.add(()=>{const visible=new Set(visibleChunks(world.x,world.y,world.scale.x,host.clientWidth,host.clientHeight,data.width_m).map(p=>p.join(',')));for(const [key,g] of chunks)g.visible=visible.has(key);});

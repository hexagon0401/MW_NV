/** Replay-time effects. No wall clock, random generator, damage or targeting decisions. */
import {Container,Sprite,Texture,Rectangle} from 'pixi.js';
const KINDS=['flash','rifle','cannon','tank','rocket','blast','dust','spark','miss','armor'];
export function weaponKind(shot,units){const actor=units.find(u=>u.id===shot.unit);return shot.weapon==='ap'?(actor?.type_id==='MBT'?'tank':'rocket'):shot.weapon==='cannon'?'cannon':['tank','rocket','autocannon'].includes(shot.weapon)?(shot.weapon==='autocannon'?'cannon':shot.weapon):'rifle';}
export function effectSamples(frame,time=frame.render_time??frame.tick/5,reduced=false){
 const out=[],add=(kind,x,y,size,phase,rotation=0,alpha=1)=>out.push({kind,x,y,size,frame:Math.max(0,Math.min(7,Math.floor(phase*8))),rotation,alpha});
 for(const shot of frame.shots??[]){const age=time-shot.tick/5;if(age<0||age>.7)continue;const a=shot.origin,b=shot.destination;if(!a||!b)continue;const kind=weaponKind(shot,frame.units),heavy=['tank','rocket'].includes(kind),travel=heavy?.14:.08,ax=a.x_cm*.12,ay=a.y_cm*.12,bx=b.x_cm*.12,by=b.y_cm*.12,angle=Math.atan2(by-ay,bx-ax);
  if(age<.08)add('flash',ax,ay,heavy?24:12,age/.08,angle);
  if(age<travel&&!reduced){const f=age/travel;add(kind,ax+(bx-ax)*f,ay+(by-ay)*f,heavy?20:12,f,angle);}
  if(age>=travel&&age<travel+.18)add(shot.hit===false?'miss':shot.damage===0?'armor':'spark',bx,by,shot.damage===0?12:18,(age-travel)/.18);
  if(heavy&&age>=.08&&age<.65&&!reduced)add('dust',ax,ay,26+(age-.08)*20,(age-.08)/.57,0,.55);
 }
 for(const impact of frame.impacts??[]){const age=time-impact.tick/5;if(age<0||age>.8)continue;const radius=(impact.blast_m??12)*12,size=radius*2;add('blast',impact.x_cm*.12,impact.y_cm*.12,size,reduced?.45:age/.8);}
 for(const p of frame.projectiles??[]){if(!p.origin||p.fired_tick==null)continue;const age=time-p.fired_tick/5,duration=(p.impact_tick-p.fired_tick)/5;if(age<0||age>duration)continue;const ax=p.origin.x_cm*.12,ay=p.origin.y_cm*.12,bx=p.x_cm*.12,by=p.y_cm*.12,f=age/duration;if(age<.12)add('flash',ax,ay,30,age/.12);if(!reduced)add('rocket',ax+(bx-ax)*f,ay+(by-ay)*f-Math.sin(f*Math.PI)*90,18,f,Math.atan2(by-ay,bx-ax));}
 return out.sort((a,b)=>Number(b.kind==='blast')-Number(a.kind==='blast')).slice(0,160);
}
export class CombatEffects{
 constructor(world){this.layer=new Container();world.addChild(this.layer);this.pool=[];const canvas=document.createElement('canvas');canvas.width=8*48;canvas.height=KINDS.length*48;const c=canvas.getContext('2d');
  const rect=(color,x,y,w,h)=>{c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),Math.max(1,Math.round(w)),Math.max(1,Math.round(h)));};
  const oval=(color,cx,cy,r)=>{for(let y=-r;y<=r;y++){const half=Math.floor(Math.sqrt(Math.max(0,r*r-y*y)));rect(color,cx-half,cy+y,half*2+1,1);}};
  for(let k=0;k<KINDS.length;k++)for(let f=0;f<8;f++){c.save();c.translate(f*48,k*48);const kind=KINDS[k],phase=f/7;
   if(kind==='flash'){const r=14-f;for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]])rect('#dca15c',24+dx*5,24+dy*5,dx?r:4,dy?r:4);rect('#fbe4a2',18,20,12,8);rect('#fff4c9',21,22,7,4);}
   else if(['rifle','cannon','tank','rocket'].includes(kind)){const heavy=kind==='tank'||kind==='rocket';rect('#765e43',8,heavy?21:23,26,heavy?6:2);rect(kind==='rocket'?'#d5a664':'#f3d694',14,heavy?21:23,20,heavy?4:2);rect('#fff0bd',31,22,5,3);if(kind==='rocket')rect('#d58c49',4,22,10,3);}
   else if(kind==='blast'){const r=5+Math.round(phase*17);oval('#818671',24,25,r);for(let j=0;j<5;j++)oval(j%2?'#a8a188':'#969a80',24+Math.round(Math.cos(j*2.5)*r*.5),24+Math.round(Math.sin(j*2.5)*r*.5),Math.round(r*.45));if(f<4){oval('#c77d40',24,23,12-f);oval('#ecaf5a',22,21,8-f);oval('#f7d88d',21,20,4);}for(let j=0;j<5;j++)rect('#bd9a62',24+Math.cos(j*2.3+f)*r,24+Math.sin(j*2.3+f)*r,2,2);}
   else if(kind==='dust'){oval('#9c9e88',23,24,6+f);oval('#b7b398',21,22,5+f);}
   else{const col=kind==='miss'?'#a5ad9c':kind==='armor'?'#a4bdc0':'#e0b66b',r=4+f;for(let j=0;j<5;j++)rect(col,24+Math.cos(j*2.4)*r,24+Math.sin(j*2.4)*r,2,2);if(f<3)rect('#fff0be',22,22,4,4);}
   c.restore();
  }
  this.base=Texture.from(canvas);this.base.source.scaleMode='nearest';this.textures=new Map();for(let k=0;k<KINDS.length;k++)for(let f=0;f<8;f++)this.textures.set(`${KINDS[k]}:${f}`,new Texture({source:this.base.source,frame:new Rectangle(f*48,k*48,48,48)}));
 }
 update(frame,time,zoom,reduced){const samples=effectSamples(frame,time,reduced);for(let i=0;i<Math.max(this.pool.length,samples.length);i++){let s=this.pool[i];if(!s){s=new Sprite();s.anchor.set(.5);this.layer.addChild(s);this.pool.push(s);}const p=samples[i];s.visible=!!p;if(!p)continue;s.texture=this.textures.get(`${p.kind}:${p.frame}`);s.position.set(p.x,p.y);s.width=s.height=p.size;s.rotation=p.rotation;s.alpha=p.alpha*(p.kind==='dust'?1-p.frame/8:1);}}
 destroy(){this.layer.destroy({children:true});for(const t of this.textures.values())t.destroy(false);this.base.destroy(true);}
}

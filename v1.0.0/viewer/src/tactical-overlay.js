import {placeBadges} from './badge-layout.js';
import {entityName,shortState,currentOrder,orderState} from './command-view.js';
import {Container,Graphics,Text} from 'pixi.js';
import {typeOf} from './catalog.js';
export const TEAM=[0x2f6fed,0xe27632];
export function groupedSquads(frame,zoom,previous=false){
 const far=zoom<=.30?true:zoom>=.36?false:previous,groups=[];
 for(const s of frame.squads??[]){const members=frame.units.filter(u=>s.member_ids.includes(u.id)&&u.alive!==false&&u.carrier_id==null);if(members.length<2)continue;
 const xs=members.map(u=>u.x_cm*.12*zoom),ys=members.map(u=>u.y_cm*.12*zoom);
 const dense=(Math.max(...xs)-Math.min(...xs)+12)*(Math.max(...ys)-Math.min(...ys)+12)<members.length*220;
 if(far||dense)groups.push({id:`squad:${s.id}`,is_group:true,team:s.team,members:members.map(u=>u.id),x_cm:members.reduce((n,u)=>n+u.x_cm,0)/members.length,y_cm:members.reduce((n,u)=>n+u.y_cm,0)/members.length,hp:members.reduce((n,u)=>n+(u.hp??0),0),max_hp:members.every(u=>u.max_hp!=null)?members.reduce((n,u)=>n+u.max_hp,0):null,name:entityName(frame,s.id),count:members.length});}
 return {far,groups};
}
export class TacticalOverlay{
 constructor(scene){this.scene=scene;this.layer=new Container();scene.world.addChild(this.layer);this.nodes=new Map();this.labels=new Map();this.far=false;}
 node(id){if(!this.nodes.has(id)){const g=new Graphics();this.layer.addChild(g);this.nodes.set(id,g);}const g=this.nodes.get(id);g.visible=true;g.clear();return g;}
 label(id,text,x,y,z){if(!this.labels.has(id)){const t=new Text({text:'',style:{fontFamily:'Geist',fontSize:11,fontWeight:'bold',fill:0x334155,stroke:{color:0xf1f2ec,width:3}}});t.anchor.set(.5);this.layer.addChild(t);this.labels.set(id,t);}const t=this.labels.get(id);t.text=text;t.position.set(x,y);t.scale.set(1/z);t.visible=true;return t;}
 update(frame){const s=this.scene,z=s.camera.zoom;for(const n of [...this.nodes.values(),...this.labels.values()])n.visible=false;
 const grouped=groupedSquads(frame,z,this.far);this.far=grouped.far;this.groups=grouped.groups;this.hidden=new Set(this.groups.flatMap(g=>g.members));
 for(const u of frame.units){const a=s.sprites.get(u.id);if(!a)continue;const infantry=typeOf(u).kind==='infantry';a.health.clear();
 if(infantry){a.sprite.visible=false;a.shadow.visible=false;a.marker.visible=false;a.badge.visible=false;}
 if(u.alive===false||u.carrier_id!=null||this.hidden.has(u.id))continue;
 const x=u.x_cm*.12,y=u.y_cm*.12,team=TEAM[u.team],g=this.node(u.id);g.position.set(x,y);g.scale.set(1/z);
 if(infantry){const r=Math.max(6,Math.min(12,6*z));g.circle(0,0,r).fill(team).stroke({width:1,color:0x243447});if(u.team===1)g.moveTo(-r,0).lineTo(r,0).stroke({width:1,color:0xf1f2ec,alpha:.5});const h=a.heading;g.moveTo(Math.cos(h)*r,Math.sin(h)*r).lineTo(Math.cos(h+.55)*(r-3),Math.sin(h+.55)*(r-3)).lineTo(Math.cos(h-.55)*(r-3),Math.sin(h-.55)*(r-3)).closePath().fill(0xfff4c1);g.circle(-Math.cos(h)*3,-Math.sin(h)*3,2).fill(0x243447);
 if(z>=1.2||s.hovered?.id===u.id)this.label(`role:${u.id}`,u.type_id,x,y+18/z,z);
 }else{g.roundRect(-12,9,24,7,2).fill(team).stroke({width:1,color:0x243447});this.label(`team:${u.id}`,u.team===0?'A':'B',x,y+12/z,z);}
 const width=infantry?24:40,height=infantry?5:6,top=infantry?-15:-Math.max(18,typeOf(u).size[1]*z/2+10),ratio=u.hp!=null&&u.max_hp>0?Math.max(0,Math.min(1,u.hp/u.max_hp)):null;
 if(ratio!=null)g.rect(-width/2-1,top-1,width+2,height+2).fill(0x182632).rect(-width/2,top,width*ratio,height).fill(ratio<=.25?0xd4483f:ratio<=.6?0xe3bc42:0x63c28a);
 }
 for(const u of this.groups){if(z<.65)continue;const x=u.x_cm*.12,y=u.y_cm*.12,g=this.node(u.id);g.position.set(x,y);g.scale.set(1/z);g.roundRect(-32,-12,64,25,4).fill(TEAM[u.team]).stroke({width:2,color:0x243447});g.rect(-32,16,64,5).fill(0x182632).rect(-32,16,64*(u.max_hp==null?0:Math.max(0,Math.min(1,u.hp/u.max_hp))),5).fill(0x63c28a);this.label(u.id,`${u.name.replace(' 분대','')} · ${u.count}`,x,y,z);}
 const semantic=[...this.groups.map(g=>({...g,name:entityName(frame,Number(g.id.split(':')[1])).replace('분대','보병')+' '+g.count,priority:1})),...frame.units.filter(u=>u.alive!==false&&u.carrier_id==null&&(typeOf(u).kind==='vehicle'||z<.3&&!this.hidden.has(u.id))).map(u=>({...u,name:entityName(frame,u.id).replace('분대','보병'),priority:u.type_id==='HEL'?3:2}))];
 this.badges=z<.65?placeBadges(semantic,s.camera,s.host.clientWidth,s.host.clientHeight):[];
 for(const b of this.badges){const g=this.node(`badge:${b.id}`),wx=(b.x-s.camera.x)/z,wy=(b.y-s.camera.y)/z;g.position.set(wx,wy);g.scale.set(1/z);g.moveTo(b.ax-b.x,b.ay-b.y).lineTo(46,18).stroke({width:1,color:TEAM[b.team],alpha:.6});g.roundRect(0,0,92,36,3).fill(0xfef5ef).stroke({width:1.5,color:TEAM[b.team]});g.rect(0,0,4,36).fill(TEAM[b.team]);const title=this.label(`badge-title:${b.id}`,b.name,wx+47/z,wy+10/z,z);if(!title.semantic){title.style.fontSize=11;title.style.fill=0x07004d;title.style.stroke={width:0};title.semantic=true;}const caption=this.label(`badge-state:${b.id}`,shortState(frame,b),wx+47/z,wy+25/z,z);if(!caption.semantic){caption.style.fontSize=10;caption.style.stroke={width:0};caption.semantic=true;}const order=currentOrder(frame,b),status=order?orderState(frame,order).kind:null;caption.style.fill=status==='combat'?0xb72e2b:status==='running'?0x2f6fed:status==='waiting'?0x9c7217:0x26413c;}
 const fighting=new Map();
 for(const shot of frame.shots??[]){if(frame.tick-shot.tick>10)continue;const target=shot.destination??frame.units.find(u=>u.id===shot.target);if(target){const key=`${Math.floor(target.x_cm/6000)},${Math.floor(target.y_cm/6000)}`;fighting.set(key,{x_cm:target.x_cm,y_cm:target.y_cm});}}
 for(const impact of frame.impacts??[])if(frame.tick-impact.tick<=10)fighting.set(`impact:${impact.unit}`,impact);
 for(const [key,p] of fighting){const x=p.x_cm*.12,y=p.y_cm*.12,g=this.node(`combat:${key}`);g.position.set(x,y);g.scale.set(1/z);g.circle(0,0,22).stroke({color:0xc33735,width:2,alpha:.6});const t=this.label(`combat:${key}`,'교전 중',x,y-28/z,z);t.style.fill=0xb72e2b;}
 for(const f of frame.facilities)if(f.kind==='OBJECTIVE'){const x=f.x_cm*.12,y=f.y_cm*.12,g=this.node(`objective:${f.id}`);g.position.set(x,y);g.scale.set(1/z);g.roundRect(-40,-23,80,22,3).fill(0xfef5ef).stroke({width:2,color:f.owner==null?0xc39a35:TEAM[f.owner]});const t=this.label(`objective:${f.id}`,entityName(frame,f.id),x,y-12/z,z);if(!t.semantic){t.style.fill=0x07004d;t.style.stroke={width:0};t.semantic=true;}}
 for(const f of frame.facilities)if(f.kind==='HQ'&&f.owner!=null){const x=f.x_cm*.12,y=f.y_cm*.12,g=this.node(`HQ:${f.id}`);g.position.set(x,y);g.scale.set(1/z);g.roundRect(-30,-17,60,22,3).fill(TEAM[f.owner]).stroke({width:2,color:0x243447});this.label(`HQ:${f.id}`,`${f.owner===0?'A':'B'} 본진`,x,y-6/z,z);}
 }
 hit(x,y){const c=this.scene.camera;for(const b of this.badges??[])if(x>=b.x&&x<=b.x+92&&y>=b.y&&y<=b.y+36)return b;for(const u of this.groups??[])if(Math.abs(x-u.x_cm*.12*c.zoom-c.x)<34&&Math.abs(y-u.y_cm*.12*c.zoom-c.y)<23)return u;return null;}
}

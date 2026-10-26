import {placeBadges,combatRegions,shortId} from './badge-layout.js';
import {entityName,shortState,currentOrder,orderState} from './command-view.js';
import {Container,Graphics,Text} from 'pixi.js';
import {typeOf} from './catalog.js';
export const TEAM=[0x2f6fed,0xe27632];
export function groupedSquads(frame,zoom,previous=false){
 const far=zoom<.18?true:zoom>=.20?false:previous,groups=[];
 for(const s of frame.squads??[]){const members=frame.units.filter(u=>s.member_ids.includes(u.id)&&u.alive!==false&&u.carrier_id==null);if(members.length<2)continue;
 const xs=members.map(u=>u.x_cm*.12*zoom),ys=members.map(u=>u.y_cm*.12*zoom);
 const dense=(Math.max(...xs)-Math.min(...xs)+24)*(Math.max(...ys)-Math.min(...ys)+24)<members.length*480;
 if(far||dense)groups.push({id:`squad:${s.id}`,is_group:true,team:s.team,members:members.map(u=>u.id),x_cm:members.reduce((n,u)=>n+u.x_cm,0)/members.length,y_cm:members.reduce((n,u)=>n+u.y_cm,0)/members.length,hp:members.reduce((n,u)=>n+(u.hp??0),0),max_hp:members.every(u=>u.max_hp!=null)?members.reduce((n,u)=>n+u.max_hp,0):null,name:entityName(frame,s.id),count:members.length});}
 return {far,groups};
}
export class TacticalOverlay{
 constructor(scene){this.scene=scene;this.layer=new Container();scene.world.addChild(this.layer);this.nodes=new Map();this.labels=new Map();this.far=false;}
 node(id){if(!this.nodes.has(id)){const g=new Graphics();this.layer.addChild(g);this.nodes.set(id,g);}const g=this.nodes.get(id);g.visible=true;g.clear();return g;}
 label(id,text,x,y,z){if(!this.labels.has(id)){const t=new Text({text:'',style:{fontFamily:'Geist, NanumSquare',fontSize:11,fontWeight:'bold',fill:0x334155,stroke:{color:0xf1f2ec,width:3}}});t.anchor.set(.5);t.resolution=this.scene.app.renderer.resolution;this.scene.screenLabels.addChild(t);this.labels.set(id,t);}const t=this.labels.get(id);t.text=text;t.position.set(x*z+this.scene.camera.x,y*z+this.scene.camera.y);t.visible=true;return t;}
 update(frame){const s=this.scene,z=s.camera.zoom;for(const n of [...this.nodes.values(),...this.labels.values()])n.visible=false;
 const grouped=groupedSquads(frame,z,this.far);this.far=grouped.far;this.groups=grouped.groups;this.hidden=new Set(this.groups.flatMap(g=>g.members));
 for(const u of frame.units){const a=s.sprites.get(u.id);if(!a)continue;const infantry=typeOf(u).kind==='infantry';a.health.clear();
 if(infantry){a.sprite.visible=false;a.shadow.visible=false;a.marker.visible=false;a.badge.visible=false;}
 if(u.alive===false||u.carrier_id!=null||this.hidden.has(u.id)||!s.detail)continue;
 const x=u.x_cm*.12,y=u.y_cm*.12,team=TEAM[u.team],g=this.node(u.id);g.position.set(x,y);g.scale.set(1/z);
 if(infantry){const r=Math.max(6,Math.min(12,6*z));g.circle(0,0,r).fill(team).stroke({width:1,color:0x243447});if(u.team===1)g.moveTo(-r,0).lineTo(r,0).stroke({width:1,color:0xf1f2ec,alpha:.5});const h=a.heading;g.moveTo(Math.cos(h)*r,Math.sin(h)*r).lineTo(Math.cos(h+.55)*(r-3),Math.sin(h+.55)*(r-3)).lineTo(Math.cos(h-.55)*(r-3),Math.sin(h-.55)*(r-3)).closePath().fill(0xfff4c1);g.circle(-Math.cos(h)*3,-Math.sin(h)*3,2).fill(0x243447);
 if(z>=1.2||s.hovered?.id===u.id)this.label(`role:${u.id}`,u.type_id,x,y+18/z,z);
 }else{g.roundRect(-12,9,24,7,2).fill(team).stroke({width:1,color:0x243447});this.label(`team:${u.id}`,u.team===0?'A':'B',x,y+12/z,z);}
 const width=infantry?24:40,height=infantry?5:6,top=infantry?-15:-Math.max(18,typeOf(u).size[1]*z/2+10),ratio=u.hp!=null&&u.max_hp>0?Math.max(0,Math.min(1,u.hp/u.max_hp)):null;
 if(ratio!=null)g.rect(-width/2-1,top-1,width+2,height+2).fill(0x182632).rect(-width/2,top,width*ratio,height).fill(ratio<=.25?0xd4483f:ratio<=.6?0xe3bc42:0x63c28a);
 }
 for(const u of this.groups){if(!s.detail)continue;const x=u.x_cm*.12,y=u.y_cm*.12,g=this.node(u.id);g.position.set(x,y);g.scale.set(1/z);g.roundRect(-32,-12,64,25,4).fill(TEAM[u.team]).stroke({width:2,color:0x243447});g.rect(-32,16,64,5).fill(0x182632).rect(-32,16,64*(u.max_hp==null?0:Math.max(0,Math.min(1,u.hp/u.max_hp))),5).fill(0x63c28a);this.label(u.id,`${u.name.replace(' 분대','')} · ${u.count}`,x,y,z);}
 const semantic=[...this.groups.map(g=>({...g,type_id:'INF',name:entityName(frame,Number(g.id.split(':')[1])),priority:1})),...frame.units.filter(u=>u.alive!==false&&u.carrier_id==null&&(typeOf(u).kind==='vehicle'||z<.3&&!this.hidden.has(u.id))).map(u=>({...u,priority:u.type_id==='HEL'?3:2}))].map(u=>({...u,short:shortId(frame,u),selected:s.selected===u.id||s.selected===Number(String(u.id).split(':')[1]),priority:(s.selected===u.id?20:u.priority)}));
 this.badges=!s.detail?placeBadges(semantic,s.camera,s.host.clientWidth,s.host.clientHeight):[];
 for(const b of this.badges){const x=(b.ax-s.camera.x)/z,y=(b.ay-s.camera.y)/z,g=this.node(`badge:${b.id}`);g.position.set(x,y);g.scale.set(1/z);const color=TEAM[b.team];g.roundRect(-11,-11,22,22,3).fill({color:0x22342e,alpha:.94}).stroke({width:b.selected?2:1.5,color:b.selected?0xfff2bc:color});drawSymbol(g,b.type_id,color);if(b.is_cluster)g.circle(8,-8,4).fill(0xe8dfc9);
 if(b.showLabel){const t=this.label(`badge-title:${b.id}`,b.label,x+(17+b.label.length*3)/z,y,z);if(!t.iconLabel){t.style.fontSize=11;t.style.fill=0xf2efdf;t.style.stroke={color:0x25372e,width:3};t.iconLabel=true;}}
 }
 this.combats=combatRegions(frame);
 for(const p of this.combats){const x=p.x_cm*.12,y=p.y_cm*.12,g=this.node(`combat:${p.id}`);g.position.set(x+18/z,y-16/z);g.scale.set(1/z);g.poly([0,-7,6,5,-6,5]).fill(0xb5483d).stroke({width:1,color:0xffe5c2});}
 const selected=frame.units.find(u=>u.id===s.selected)??this.groups.find(u=>Number(String(u.id).split(':')[1])===s.selected||u.id===s.selected);
 if(selected){const x=selected.x_cm*.12,y=selected.y_cm*.12,g=this.node('selection');g.position.set(x,y);g.circle(0,0,16/z).stroke({width:2/z,color:0xffedb0});const order=currentOrder(frame,selected),target=order&&(frame.facilities.find(f=>f.id===order.target)??frame.units.find(u=>u.id===order.target));const p=target??(order?.arg0!=null&&[2,7,10,14].includes(order.op)?{x_cm:order.arg0*100,y_cm:order.arg1*100}:null);if(p)g.moveTo(0,0).lineTo(p.x_cm*.12-x,p.y_cm*.12-y).stroke({width:1/z,color:TEAM[selected.team],alpha:.7});}
 for(const f of frame.facilities)if(f.kind==='OBJECTIVE'){const x=f.x_cm*.12,y=f.y_cm*.12,g=this.node(`objective:${f.id}`);g.position.set(x,y);g.scale.set(1/z);g.roundRect(-30,-20,60,16,2).fill(0xfef5ef).stroke({width:2,color:f.owner==null?0xc39a35:TEAM[f.owner]});const t=this.label(`objective:${f.id}`,entityName(frame,f.id),x,y-12/z,z);if(!t.semantic){t.style.fill=0x07004d;t.style.stroke={width:0};t.semantic=true;}}
 for(const f of frame.facilities)if(f.kind==='HQ'&&f.owner!=null){const x=f.x_cm*.12,y=f.y_cm*.12,g=this.node(`HQ:${f.id}`);g.position.set(x,y);g.scale.set(1/z);g.roundRect(-30,-17,60,22,3).fill(TEAM[f.owner]).stroke({width:2,color:0x243447});this.label(`HQ:${f.id}`,`${f.owner===0?'A':'B'} 본진`,x,y-6/z,z);}
 }
 hit(x,y){const c=this.scene.camera;for(const b of this.badges??[])if(Math.abs(x-b.ax)<=13&&Math.abs(y-b.ay)<=13)return b;for(const u of this.groups??[])if(this.scene.detail&&Math.abs(x-u.x_cm*.12*c.zoom-c.x)<34&&Math.abs(y-u.y_cm*.12*c.zoom-c.y)<23)return u;return null;}
}
function drawSymbol(g,type,color){
 const r=(x,y,w,h)=>g.rect(x,y,w,h).fill(color);
 if(type==='HEL'){r(-7,-2,14,4);r(-5,-8,1,16);r(5,-8,1,16);r(-8,-6,7,1);r(2,5,7,1);}
 else if(['MBT','SPH','IFV'].includes(type)){r(-7,-5,13,2);r(-7,4,13,2);r(-5,-3,9,6);r(0,-1,type==='SPH'?10:9,2);}
 else if(['TRK','APC','LUV'].includes(type)){r(-7,-4,9,8);r(3,-3,4,6);r(-5,-6,3,2);r(3,-5,3,2);r(-5,4,3,2);r(3,3,3,2);}
 else{g.circle(-2,-2,3).fill(color);r(-5,2,7,3);r(2,-3,6,2);}
}

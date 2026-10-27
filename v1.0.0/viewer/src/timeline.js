/** Read-side projection only: input replay and engine state are never mutated. */
export class Timeline{
 constructor(data){this.data=data;this.startTime=(data.initial.tick??0)/5;this.duration=(data.final?.tick??0)/5;this.tracks=new Map();
  for(const u of data.initial.units)this.tracks.set(u.id,[{t:this.startTime,x:u.x_cm,y:u.y_cm}]);
  for(const e of data.events){const p=e.payload,t=(e.sim_tick+1)/5;if(t<=this.startTime)continue;
   if(e.event_kind==='UNIT_SPAWNED'&&p.entity)this.tracks.set(p.unit,[{t,x:p.entity.x_cm,y:p.entity.y_cm}]);
   if(['UNIT_MOVED','DISEMBARK_DONE'].includes(e.event_kind)&&p.x_cm!==undefined)this.tracks.get(p.unit)?.push({t,x:p.x_cm,y:p.y_cm});
  }this.reset();
 }
 reset(){this.state=structuredClone(this.data.initial);this.units=new Map(this.state.units.map(u=>[u.id,u]));this.unknownPassengers=new Map(this.state.units.filter(u=>u.passenger_count!=null).map(c=>[c.id,Math.max(0,c.passenger_count-this.state.units.filter(u=>u.carrier_id===c.id).length)]));this.facilities=new Map(this.state.facilities.map(f=>[f.id,f]));this.commands=new Map((this.state.orders??[]).map(c=>[`${c.team}:${c.cmd_id}`,{...c}]));this.index=0;while(this.index<this.data.events.length&&(this.data.events[this.index].sim_tick+1)/5<=this.startTime)this.index++;this.lastTime=-1;}
 apply(e){const p=e.payload,u=this.units.get(p.unit),f=this.facilities.get(p.objective),kind=e.event_kind;
  if(kind==='UNIT_SPAWNED'&&p.entity){const unit=structuredClone(p.entity);if(Array.isArray(unit.passenger_ids)){unit.passenger_count=unit.passenger_ids.length;this.unknownPassengers.set(unit.id,0);}this.units.set(unit.id,unit);if(p.squad){this.state.squads=(this.state.squads??[]).filter(s=>s.id!==p.squad.id);this.state.squads.push(structuredClone(p.squad));}}
  if(kind==='VEHICLE_WAITING'&&u)u.task_state='WAITING_TRAFFIC';
  if(kind==='UNIT_MOVED'&&u){u.task_state='MOVING';u.x_cm=p.x_cm;u.y_cm=p.y_cm;}
  if(kind==='UNIT_ARRIVED'&&u){u.task_state='ARRIVED';for(const s of this.state.squads??[])if(s.member_ids.includes(u.id))for(const id of s.member_ids){const member=this.units.get(id);if(member?.alive&&member.carrier_id==null)member.task_state='ARRIVED';}}
  if(['INFANTRY_DISABLED','VEHICLE_DISABLED'].includes(kind)&&u){u.alive=false;u.task_state='DISABLED';}
  if(kind==='EMPLACEMENT_CAPTURED'&&u){u.team=p.team;const crew=this.units.get(p.crew);if(crew)crew.carrier_id=p.unit;}
  if(kind==='EMPLACEMENT_INACTIVE'&&u&&u.alive!==false)u.team=null;
  if(kind==='EMPLACEMENT_LEFT'){const v=this.units.get(p.vehicle);if(v)v.team=null;}
  const flags=this.state.mission?.flags,flag=flags?.[p.owner];
  if(flag&&['FLAG_STOLEN','FLAG_PICKED_UP'].includes(kind)){flag.status='carried';flag.carrier=p.carrier;}
  if(flag&&kind==='FLAG_DROPPED'){flag.status='dropped';flag.carrier=null;flag.x_cm=p.x_cm;flag.y_cm=p.y_cm;}
  if(flag&&kind==='FLAG_RETURNED'){flag.status='home';flag.carrier=null;[flag.x_cm,flag.y_cm]=flag.home;}
  if(kind==='EMBARK_DONE'&&u){u.carrier_id=p.vehicle;u.task_state='ONBOARD';}
  if(kind==='DISEMBARK_DONE'&&u){u.carrier_id=null;u.task_state='IDLE';}
  if(kind==='ABSTRACT_ATTACK'&&u){if(p.ammo!=null)u.ammo=p.ammo;else if(u.ammo!=null)u.ammo=Math.max(0,u.ammo-1);u.attack_tick=e.sim_tick+1;u.target_id=p.target;const target=this.units.get(p.target);if(target&&target.hp!=null)target.hp=p.target_hp??Math.max(0,target.hp-p.damage);(this.state.shots??=[]).push({...p,origin:p.origin??{x_cm:u.x_cm,y_cm:u.y_cm},destination:p.destination??(target?{x_cm:target.x_cm,y_cm:target.y_cm}:null),tick:e.sim_tick+1});}
  if(kind==='UNIT_TASK_CHANGED'&&u){u.task_state=p.task_state;if(p.deployment)u.deployment=p.deployment;}
  if(kind==='UNIT_DAMAGED'&&u)u.hp=p.hp;
  if(kind==='UNIT_RESUPPLIED'&&u)for(const name of ['ammo','fuel','heal_pool','repair_pool'])if(p[name]!=null)u[name]=p[name];
  if(kind==='SUPPLY_CHANGED'&&p.vehicle!=null&&p.cargo_supply!=null){const truck=this.units.get(p.vehicle);if(truck)truck.cargo_supply=p.cargo_supply;}
  if(kind==='UNIT_REPAIRED'&&u)u.hp=p.hp;
  if(kind==='UNIT_HEALED'&&u&&u.hp!=null)u.hp+=p.amount;
  if(kind==='DEPLOYMENT_CHANGED'&&u)u.deployment=p.deployment;
  if(kind==='ARTILLERY_FIRED'){(this.state.projectiles??=[]).push({...p,fired_tick:p.fired_tick==null?undefined:p.fired_tick+1,impact_tick:p.impact_tick+1});if(u)u.ammo=p.ammo??null;}
  if(['ARTILLERY_IMPACT','TANK_IMPACT'].includes(kind))(this.state.impacts??=[]).push({...p,tick:e.sim_tick+1});
  if(kind==='UNIT_DAMAGED'&&p.damage)(this.state.damage??=[]).push({...p,tick:e.sim_tick+1});
  if(kind==='HQ_DECISION')(this.state.decisions??={})[p.team]=structuredClone(p.metadata);
  if(kind==='SUPPLY_CHANGED'&&p.team!=null&&this.state.mission?.teams?.[p.team])for(const [key,value] of Object.entries(p.costs??{}))this.state.mission.teams[p.team][key]-=value;
  if(kind==='COMBAT_TICKETS_CHANGED'&&this.state.mission?.combat_tickets)this.state.mission.combat_tickets[p.team]=p.remaining;
  if(kind==='FLAG_STOLEN'&&p.score!=null)this.state.scores[p.team]=p.score;
  if(kind==='SCORE_TICK')this.state.scores={...p.scores};
  if(kind.startsWith('ORDER_')&&p.cmd_id!==undefined&&p.team!==undefined){const key=`${p.team}:${p.cmd_id}`,old=this.commands.get(key);this.commands.set(key,{...old,...p,status:kind.slice(6),accepted_tick:old?.accepted_tick??e.sim_tick});}
  if(f){if(kind==='CAPTURE_PROGRESS'){f.progress_ms=p.progress_ms;f.capturing=p.team;}if(kind==='OBJECTIVE_CAPTURED'){f.owner=p.team;f.progress_ms=0;f.capturing=null;}if(kind==='OBJECTIVE_NEUTRALIZED'){f.owner=null;f.progress_ms=0;}}
 }
 at(seconds){const t=Math.max(this.startTime,Math.min(this.duration,seconds));if(t<this.lastTime)this.reset();
  while(this.index<this.data.events.length&&(this.data.events[this.index].sim_tick+1)/5<=t)this.apply(this.data.events[this.index++]);this.lastTime=t;
  const units=[...this.units.values()].map(unit=>{const u={...unit},track=this.tracks.get(u.id);if(track?.length){let lo=0,hi=track.length;while(lo+1<hi){const m=(lo+hi)>>1;if(track[m].t<=t)lo=m;else hi=m;}const a=track[lo],b=track[lo+1],f=b?Math.max(0,Math.min(1,(t-a.t)/(b.t-a.t||1))):0;u.x_cm=a.x+(b?b.x-a.x:0)*f;u.y_cm=a.y+(b?b.y-a.y:0)*f;}if(u.activity_until_tick!==undefined&&t*5>=u.activity_until_tick)u.activity=null;if(u.alive!==false&&u.carrier_id==null&&u.attack_tick!==undefined&&t*5-u.attack_tick<10)u.activity='FIRING';return u;});
  const byId=new Map(units.map(u=>[u.id,u]));
  for(const carrier of units)if(carrier.passenger_count!=null)carrier.passenger_count=carrier.alive===false?0:(this.unknownPassengers.get(carrier.id)??0)+units.filter(u=>u.carrier_id===carrier.id&&u.alive!==false).length;for(const u of units)if(u.carrier_id!=null){const carrier=byId.get(u.carrier_id);if(carrier){u.x_cm=carrier.x_cm;u.y_cm=carrier.y_cm;}}
  return {...this.state,mission:this.state.mission?structuredClone(this.state.mission):undefined,projectiles:(this.state.projectiles??[]).filter(s=>s.impact_tick>=t*5),impacts:(this.state.impacts??[]).filter(s=>t*5-s.tick<=10),damage:(this.state.damage??[]).filter(s=>t*5-s.tick<=10),shots:(this.state.shots??[]).filter(s=>t*5-s.tick<=10),tick:Math.round(t*5),render_time:t,units,scores:{...this.state.scores},facilities:[...this.facilities.values()].map(f=>({...f})),orders:[...this.commands.values()].map(c=>({...c}))};
 }
}

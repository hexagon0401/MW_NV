/** Read-side projection only: input replay and engine state are never mutated. */
export class Timeline{
 constructor(data){this.data=data;this.duration=(data.final?.tick??0)/5;this.tracks=new Map();
  for(const u of data.initial.units)this.tracks.set(u.id,[{t:0,x:u.x_cm,y:u.y_cm}]);
  for(const e of data.events){const p=e.payload,t=(e.sim_tick+1)/5;
   if(e.event_kind==='UNIT_SPAWNED'&&p.entity)this.tracks.set(p.unit,[{t,x:p.entity.x_cm,y:p.entity.y_cm}]);
   if(['UNIT_MOVED','DISEMBARK_DONE'].includes(e.event_kind)&&p.x_cm!==undefined)this.tracks.get(p.unit)?.push({t,x:p.x_cm,y:p.y_cm});
  }this.reset();
 }
 reset(){this.state=structuredClone(this.data.initial);this.units=new Map(this.state.units.map(u=>[u.id,u]));this.facilities=new Map(this.state.facilities.map(f=>[f.id,f]));this.commands=new Map();this.index=0;this.lastTime=-1;}
 apply(e){const p=e.payload,u=this.units.get(p.unit),f=this.facilities.get(p.objective),kind=e.event_kind;
  if(kind==='UNIT_SPAWNED'&&p.entity){const unit=structuredClone(p.entity);this.units.set(unit.id,unit);}
  if(kind==='UNIT_MOVED'&&u)u.task_state='MOVING';
  if(kind==='UNIT_ARRIVED'&&u){u.task_state='ARRIVED';for(const s of this.state.squads??[])if(s.member_ids.includes(u.id))for(const id of s.member_ids){const member=this.units.get(id);if(member?.alive&&member.carrier_id==null)member.task_state='ARRIVED';}}
  if(kind==='INFANTRY_DISABLED'&&u){u.alive=false;u.task_state='DISABLED';}
  if(kind==='EMBARK_DONE'&&u){u.carrier_id=p.vehicle;u.task_state='ONBOARD';}
  if(kind==='DISEMBARK_DONE'&&u){u.carrier_id=null;u.task_state='IDLE';}
  if(kind==='ABSTRACT_ATTACK'&&u)u.attack_tick=e.sim_tick;
  if(kind==='SCORE_TICK')this.state.scores={...p.scores};
  if(kind.startsWith('ORDER_')&&p.cmd_id!==undefined&&p.team!==undefined){const key=`${p.team}:${p.cmd_id}`,old=this.commands.get(key);this.commands.set(key,{...old,...p,status:kind.slice(6),accepted_tick:old?.accepted_tick??e.sim_tick});}
  if(f){if(kind==='CAPTURE_PROGRESS'){f.progress_ms=p.progress_ms;f.capturing=p.team;}if(kind==='OBJECTIVE_CAPTURED'){f.owner=p.team;f.progress_ms=0;f.capturing=null;}if(kind==='OBJECTIVE_NEUTRALIZED'){f.owner=null;f.progress_ms=0;}}
 }
 at(seconds){const t=Math.max(0,Math.min(this.duration,seconds));if(t<this.lastTime)this.reset();
  while(this.index<this.data.events.length&&(this.data.events[this.index].sim_tick+1)/5<=t)this.apply(this.data.events[this.index++]);this.lastTime=t;
  const units=[...this.units.values()].map(unit=>{const u={...unit},track=this.tracks.get(u.id);if(track?.length){let lo=0,hi=track.length;while(lo+1<hi){const m=(lo+hi)>>1;if(track[m].t<=t)lo=m;else hi=m;}const a=track[lo],b=track[lo+1],f=b?Math.max(0,Math.min(1,(t-a.t)/(b.t-a.t||1))):0;u.x_cm=a.x+(b?b.x-a.x:0)*f;u.y_cm=a.y+(b?b.y-a.y:0)*f;}if(u.alive!==false&&u.carrier_id==null&&u.attack_tick!==undefined&&t*5-u.attack_tick<10)u.task_state='FIRING';return u;});
  const byId=new Map(units.map(u=>[u.id,u]));for(const u of units)if(u.carrier_id!=null){const carrier=byId.get(u.carrier_id);if(carrier){u.x_cm=carrier.x_cm;u.y_cm=carrier.y_cm;}}
  return {...this.state,tick:Math.round(t*5),units,scores:{...this.state.scores},facilities:[...this.facilities.values()].map(f=>({...f})),orders:[...this.commands.values()].map(c=>({...c}))};
 }
}

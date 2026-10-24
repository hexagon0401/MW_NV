export class Timeline {
 constructor(data){this.data=data;this.duration=(data.final?.tick??0)/5;this.tracks=new Map();for(const u of data.initial.units)this.tracks.set(u.id,[{t:0,x:u.x_cm,y:u.y_cm}]);for(const e of data.events){if(e.event_kind==='UNIT_MOVED'||e.event_kind==='DISEMBARK_DONE'){const p=e.payload;if(p.x_cm!==undefined)this.tracks.get(p.unit)?.push({t:(e.sim_tick+1)/5,x:p.x_cm,y:p.y_cm});}}}
 at(seconds){const t=Math.max(0,Math.min(this.duration,seconds));const frame=structuredClone(this.data.initial);frame.tick=Math.round(t*5);frame.orders=[];
  for(const u of frame.units){const track=this.tracks.get(u.id);let lo=0,hi=track.length;while(lo+1<hi){const m=(lo+hi)>>1;if(track[m].t<=t)lo=m;else hi=m;}const a=track[lo],b=track[lo+1];const f=b?Math.max(0,Math.min(1,(t-a.t)/(b.t-a.t||1))):0;u.x_cm=a.x+(b?b.x-a.x:0)*f;u.y_cm=a.y+(b?b.y-a.y:0)*f;}
  const byId=new Map(frame.units.map(u=>[u.id,u]));
  for(const e of this.data.events){if((e.sim_tick+1)/5>t)break;const p=e.payload;
   if(e.event_kind==='UNIT_SPAWNED'&&p.entity){const u=structuredClone(p.entity);frame.units.push(u);byId.set(u.id,u);}
   if(e.event_kind==='SCORE_TICK')frame.scores=p.scores;
   if(e.event_kind==='ORDER_ACCEPTED'||e.event_kind==='ORDER_COMPLETED'||e.event_kind==='ORDER_FAILED'||e.event_kind==='ORDER_CANCELLED')frame.orders.push({team:p.team,cmd_id:p.cmd_id,status:e.event_kind,op:p.op});
   if(e.event_kind==='INFANTRY_DISABLED'&&byId.has(p.unit))byId.get(p.unit).alive=false;
   if(e.event_kind==='EMBARK_DONE'&&byId.has(p.unit))byId.get(p.unit).carrier_id=p.vehicle;
   if(e.event_kind==='DISEMBARK_DONE'&&byId.has(p.unit))byId.get(p.unit).carrier_id=null;
   const objective=frame.facilities.find(f=>f.id===p.objective);
   if(objective){if(e.event_kind==='CAPTURE_PROGRESS')objective.progress_ms=p.progress_ms;if(e.event_kind==='OBJECTIVE_CAPTURED'){objective.owner=p.team;objective.progress_ms=0;}if(e.event_kind==='OBJECTIVE_NEUTRALIZED'){objective.owner=null;objective.progress_ms=0;}}
  }
  for(const u of frame.units){if(u.carrier_id!==null){const carrier=byId.get(u.carrier_id);if(carrier){u.x_cm=carrier.x_cm;u.y_cm=carrier.y_cm;}}}
  frame.orders=frame.orders.slice(-10);return frame;
 }
}

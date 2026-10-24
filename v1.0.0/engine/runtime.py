"""Network-free fixed-step simulation. All times accumulate in integer ms."""
from decimal import Decimal
from dataclasses import replace
from .orders import CommandQueue, OrderError
from .state import WorldState
from .types import Op, Team, Command
from .movement import move
from .infantry import move_squad
from .sensing import update_sensing, observation
from .combat import update_combat
from .logistics import resupply, heal, regenerate
from .transport import move_vehicle, embark, unload, release_transfer_locks
from .objectives import update_capture, update_score


class Engine:
    def __init__(self, world=None):
        self.world = world if world is not None else WorldState()
        if self.world.config.tick_s != 0.2:
            raise ValueError('engine tick must be 0.2 seconds')
        if not hasattr(self.world, 'queue'):
            self.world.queue = CommandQueue()
            self.world.remainder_ms = 0

    def submit(self, command):
        try:
            return self.world.queue.submit(self.world, command)
        except OrderError as exc:
            self.world.emit('ORDER_REJECTED', reason=str(exc))
            raise

    def submit_for(self,team,command):
        """Authenticated policy boundary: a policy may only submit its own team."""
        team=Team(team)
        if not isinstance(command,(dict,Command)):
            raise OrderError('SCHEMA_ERROR')
        claimed=command.get('team') if isinstance(command,dict) else command.team
        if claimed!=team:
            self.world.emit('ORDER_REJECTED',team=int(team),reason='FOREIGN_TEAM')
            raise OrderError('FOREIGN_TEAM')
        return self.submit(command)

    def step(self, dt=0.2):
        ms = Decimal(str(dt)) * 1000
        if not ms.is_finite() or ms < 0 or ms != ms.to_integral_value():
            raise ValueError('dt must be nonnegative whole milliseconds')
        w = self.world
        if getattr(w,"ended",False):
            return []
        begin = len(w.events)
        w.remainder_ms += int(ms)
        while w.remainder_ms >= 200 and not getattr(w,"ended",False):
            w.remainder_ms -= 200
            self._tick()
            w.tick += 1
        if getattr(w,"ended",False):
            w.remainder_ms=0
        return w.events[begin:]

    def _tick(self):
        w = self.world
        release_transfer_locks(w)
        ready=w.queue.ready(w)
        # Resolve replacement orders before moving anything during this tick.
        winners={}
        for key,c in ready:
            if c.op in (Op.WAIT,Op.CANCEL):continue
            actor=(c.team,c.unit)
            if actor not in winners or (c.priority,c.tick,c.cmd_id)>winners[actor][0]:
                winners[actor]=((c.priority,c.tick,c.cmd_id),key)
        for key,c in ready:
            if c.op not in (Op.WAIT,Op.CANCEL) and winners[(c.team,c.unit)][1]!=key:
                w.queue.finish(w,key,'CANCELLED')
        for key, c in ready:
            if w.queue.status[key] not in ('QUEUED', 'RUNNING'):
                continue
            try:
                self._execute(key, c)
            except OrderError as exc:
                w.queue.finish(w, key, 'FAILED', str(exc))

        if (w.tick+1) % 5 == 0:
            update_sensing(w)
        update_combat(w)
        update_capture(w)
        update_score(w)
        regenerate(w)

    def observe(self,team):
        return observation(self.world,team)

    def _execute(self, key, c):
        w = self.world
        if c.op in (Op.RESUPPLY,Op.HEAL):
            w.queue.status[key]="RUNNING"
            if (resupply if c.op==Op.RESUPPLY else heal)(w,key,c):w.queue.finish(w,key)
            return
        if c.op==Op.DISEMBARK:
            w.queue.status[key]="RUNNING"
            if unload(w,key,c):w.queue.finish(w,key)
            return
        if c.op==Op.EMBARK:
            w.queue.status[key]="RUNNING"
            if embark(w,key,c):w.queue.finish(w,key)
            return
        if c.op in (Op.CAPTURE,Op.DEFEND):
            f=w.facilities[c.target]
            if f.kind != "OBJECTIVE":
                raise OrderError("INVALID_TARGET")
            c=replace(c,op=Op.MOVE,arg0=f.pos.x_cm//100,arg1=f.pos.y_cm//100)
        if c.op in (Op.MOVE,Op.TRANSPORT) and c.unit in w.vehicles:
            w.queue.status[key]="RUNNING"
            if not move_vehicle(w,key,w.vehicles[c.unit],(c.arg0*100,c.arg1*100)):
                return
            w.queue.finish(w,key)
            return
        if c.op in (Op.MOVE, Op.RETREAT):
            unit = w.soldiers.get(c.unit)
            if c.unit in w.squads:
                w.queue.status[key] = 'RUNNING'
                if not move_squad(w,key,w.squads[c.unit],(c.arg0*100,c.arg1*100)):
                    return
                w.queue.finish(w,key)
                return
            if unit is None or not unit.alive or unit.carrier_id is not None:
                raise OrderError('ILLEGAL_STATE')
            if w.queue.status[key] == 'QUEUED':
                for other, cmd in w.queue.commands.items():
                    if other != key and cmd.unit == c.unit and w.queue.status[other] == 'RUNNING':
                        w.queue.finish(w, other, 'CANCELLED')
                w.queue.status[key] = 'RUNNING'
            if not move(w,key,unit,(c.arg0*100,c.arg1*100),w.unit_specs[unit.type_id]["speed_mps"]):
                return
        elif c.op == Op.CANCEL:
            w.queue.cancel(w, c.team, c.target)
        elif c.op==Op.HOLD:
            ids=w.squads[c.unit].member_ids if c.unit in w.squads else [c.unit]
            for id in ids:
                unit=w.soldiers.get(id)
                if unit is not None and unit.alive and unit.carrier_id is None:unit.task_state='HOLD'
        elif c.op != Op.WAIT:
            raise OrderError('UNSUPPORTED_OP')
        w.queue.finish(w, key)

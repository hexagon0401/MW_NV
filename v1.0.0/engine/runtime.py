"""Network-free fixed-step simulation. All times accumulate in integer ms."""
from decimal import Decimal
from dataclasses import replace
from .orders import CommandQueue, OrderError
from .state import WorldState
from .types import Op
from .movement import move
from .infantry import move_squad
from .sensing import update_sensing, observation
from .combat import update_combat
from .objectives import update_capture


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

    def step(self, dt=0.2):
        ms = Decimal(str(dt)) * 1000
        if not ms.is_finite() or ms < 0 or ms != ms.to_integral_value():
            raise ValueError('dt must be nonnegative whole milliseconds')
        w = self.world
        begin = len(w.events)
        w.remainder_ms += int(ms)
        while w.remainder_ms >= 200:
            w.remainder_ms -= 200
            self._tick()
            w.tick += 1
        return w.events[begin:]

    def _tick(self):
        w = self.world
        for key, c in w.queue.ready(w):
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

    def observe(self,team):
        return observation(self.world,team)

    def _execute(self, key, c):
        w = self.world
        if c.op in (Op.CAPTURE,Op.DEFEND):
            f=w.facilities[c.target]
            if f.kind != "OBJECTIVE":
                raise OrderError("INVALID_TARGET")
            c=replace(c,op=Op.MOVE,arg0=f.pos.x_cm//100,arg1=f.pos.y_cm//100)
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
        elif c.op not in (Op.WAIT, Op.HOLD):
            raise OrderError('UNSUPPORTED_OP')
        w.queue.finish(w, key)

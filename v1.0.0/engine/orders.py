"""Validated integer command boundary; game agents cannot execute code."""
from dataclasses import fields
from enum import IntEnum
from collections.abc import MutableMapping
from .types import Command, Team, Op


class OrderError(ValueError):
    pass


def parse_command(raw):
    if not isinstance(raw, dict) or set(raw) - {f.name for f in fields(Command)}:
        raise OrderError('SCHEMA_ERROR')
    if any(type(v) is not int for v in raw.values()):
        raise OrderError('SCHEMA_ERROR')
    if not {'cmd_id', 'team', 'op'} <= raw.keys():
        raise OrderError('SCHEMA_ERROR')
    try:
        team = Team(raw['team'])
    except ValueError:
        raise OrderError('SCHEMA_ERROR') from None
    try:
        op = Op(raw['op'])
    except ValueError:
        raise OrderError('UNKNOWN_OP') from None
    c = Command(**(raw | {'team': team, 'op': op}))
    if c.v != 1 or c.cmd_id < 1 or c.tick < 0 or c.ttl <= 0:
        raise OrderError('SCHEMA_ERROR')
    return c


def validate(world, command):
    if not isinstance(command,(dict,Command)):
        raise OrderError('SCHEMA_ERROR')
    c = parse_command(command if isinstance(command, dict) else {
        f.name: (int(getattr(command, f.name)) if isinstance(getattr(command, f.name),IntEnum) else getattr(command, f.name)) for f in fields(Command)})
    if c.tick + c.ttl <= world.tick:
        raise OrderError('EXPIRED')
    if c.op==Op.PURCHASE:
        from .economy import PURCHASE_TYPES
        if not 0<=c.arg0<len(PURCHASE_TYPES):raise OrderError('INVALID_TARGET')
        hq=world.facilities.get(c.target)
        if hq is None or hq.kind!='HQ':raise OrderError('INVALID_TARGET')
        if hq.owner!=c.team:raise OrderError('FOREIGN_UNIT')
        return c
    if c.op in (Op.WAIT, Op.CANCEL):
        return c
    unit = world.soldiers.get(c.unit) or world.squads.get(c.unit) or world.vehicles.get(c.unit)
    if unit is None:
        raise OrderError('INVALID_TARGET')
    if unit.team != c.team:
        raise OrderError('FOREIGN_UNIT')
    if c.op in (Op.MOVE, Op.RETREAT, Op.TRANSPORT, Op.DISEMBARK):
        if not (0 <= c.arg0 < world.config.map_width_m and 0 <= c.arg1 < world.config.map_height_m):
            raise OrderError('OUT_OF_BOUNDS')
    if c.op in (Op.CAPTURE, Op.DEFEND, Op.RESUPPLY) and c.target not in world.facilities and not (c.op==Op.RESUPPLY and c.target in world.vehicles):
        raise OrderError('INVALID_TARGET')
    return c


class TeamMap(MutableMapping):
    """Physically separate team stores behind the engine's indexed interface."""
    def __init__(self):
        self.by_team={'0':{},'1':{}}

    def _store(self,key):return self.by_team[key.split(':',1)[0]]
    def __getitem__(self,key):return self._store(key)[key]
    def __setitem__(self,key,value):self._store(key)[key]=value
    def __delitem__(self,key):del self._store(key)[key]
    def __iter__(self):
        for store in self.by_team.values():yield from store
    def __len__(self):return sum(map(len,self.by_team.values()))


class CommandQueue:
    def __init__(self):
        self.commands = TeamMap()
        self.status = TeamMap()

    def submit(self, world, raw):
        c = validate(world, raw)
        key = f'{int(c.team)}:{c.cmd_id}'
        if key in self.commands:
            if self.commands[key] != c:
                raise OrderError('DUPLICATE_ID')
            return key
        self.commands[key] = c
        self.status[key] = 'QUEUED'
        world.emit('ORDER_ACCEPTED', team=int(c.team), cmd_id=c.cmd_id)
        return key

    def finish(self, world, key, status='COMPLETED', reason=None):
        if self.status[key] not in ('QUEUED', 'RUNNING'):
            return
        self.status[key] = status
        c = self.commands[key]
        world.emit('ORDER_' + status, team=int(c.team), cmd_id=c.cmd_id, reason=reason)

    def ready(self, world):
        result = []
        for key, c in self.commands.items():
            if self.status[key] not in ('QUEUED', 'RUNNING'):
                continue
            if c.tick + c.ttl <= world.tick:
                self.finish(world, key, 'FAILED', 'EXPIRED')
            elif c.tick <= world.tick:
                result.append((key, c))
        return sorted(result, key=lambda item: (-item[1].priority, item[1].tick, int(item[1].team), item[1].cmd_id))

    def cancel(self, world, team, cmd_id):
        key = f'{int(team)}:{cmd_id}'
        if key not in self.commands:
            raise OrderError('INVALID_TARGET')
        self.finish(world, key, 'CANCELLED')

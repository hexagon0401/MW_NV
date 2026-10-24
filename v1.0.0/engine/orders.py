"""Validated integer command boundary; game agents cannot execute code."""
from dataclasses import fields
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
    c = parse_command(command if isinstance(command, dict) else {
        f.name: int(getattr(command, f.name)) for f in fields(Command)})
    if c.tick + c.ttl <= world.tick:
        raise OrderError('EXPIRED')
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
    if c.op in (Op.CAPTURE, Op.DEFEND, Op.RESUPPLY) and c.target not in world.facilities:
        raise OrderError('INVALID_TARGET')
    return c


class CommandQueue:
    def __init__(self):
        self.commands = {}
        self.status = {}

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

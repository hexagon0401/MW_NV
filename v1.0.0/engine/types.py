"""Game-only entities. Positions are integer centimetres; IDs are global."""
from dataclasses import dataclass, field, asdict
from enum import IntEnum


class Team(IntEnum):
    A = 0
    B = 1


class Op(IntEnum):
    WAIT = 0
    HOLD = 1
    MOVE = 2
    CAPTURE = 3
    DEFEND = 4
    EMBARK = 5
    DISEMBARK = 6
    TRANSPORT = 7
    RESUPPLY = 8
    HEAL = 9
    RETREAT = 10
    PURCHASE = 11
    CANCEL = 12


def natural(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name)


@dataclass(frozen=True)
class WorldPos:
    x_cm: int
    y_cm: int

    def __post_init__(self):
        natural(self.x_cm, 'x_cm')
        natural(self.y_cm, 'y_cm')


@dataclass
class Entity:
    id: int
    team: Team
    pos: WorldPos

    def __post_init__(self):
        natural(self.id, 'id', 1)
        if not isinstance(self.team, Team) or not isinstance(self.pos, WorldPos):
            raise ValueError('team/pos')

    def to_dict(self):
        return asdict(self)


@dataclass
class Soldier(Entity):
    type_id: str = 'INF'
    hp: int = 100
    ammo: int = 30
    alive: bool = True
    squad_id: int | None = None
    carrier_id: int | None = None
    task_state: str = 'IDLE'
    target_id: int | None = None
    cooldown_ms: int = 0
    heal_pool: int = 0
    repair_pool: int = 0

    def __post_init__(self):
        super().__post_init__()
        if self.type_id not in ('INF', 'REC', 'SUP', 'MED', 'ENG'):
            raise ValueError('type_id')
        natural(self.hp, 'hp')
        natural(self.ammo, 'ammo')


@dataclass
class Squad(Entity):
    member_ids: list[int] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not 1 <= len(self.member_ids) <= 5 or len(set(self.member_ids)) != len(self.member_ids):
            raise ValueError('members')
        for member in self.member_ids:
            natural(member, 'member', 1)


@dataclass
class Vehicle(Entity):
    type_id: str = 'APC'
    fuel: float = 100
    passenger_ids: list[int] = field(default_factory=list)
    cargo_supply: int = 0
    task_state: str = 'IDLE'

    def __post_init__(self):
        super().__post_init__()
        if self.type_id not in ('LUV', 'APC', 'IFV', 'HEL', 'TRK'):
            raise ValueError('type_id')


@dataclass
class Facility:
    id: int
    pos: WorldPos
    kind: str = 'OBJECTIVE'
    owner: Team | None = None
    radius_cm: int = 1000
    progress_ms: int = 0
    capturing: Team | None = None


@dataclass
class TeamState:
    credits: int = 1000
    tickets: int = 70
    supply: int = 300
    score: int = 0


@dataclass(frozen=True)
class Command:
    cmd_id: int
    team: Team
    op: Op
    unit: int = 0
    arg0: int = 0
    arg1: int = 0
    target: int = 0
    tick: int = 0
    ttl: int = 600
    priority: int = 0
    v: int = 1

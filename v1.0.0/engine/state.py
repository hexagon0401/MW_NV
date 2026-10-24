"""Deterministic state, including RNG state in clones and checksums."""
from dataclasses import asdict
from copy import deepcopy
import hashlib
import json
import random
from .config import GameConfig
from .catalog import load_units
from .map import Terrain, alpha_terrain
from .types import Soldier, Team, TeamState, WorldPos, Facility


class WorldState:
    def __init__(self, seed=0, config=None):
        self.config = config or GameConfig(128, 128, 0.2)
        self.unit_specs = load_units()
        self.seed = seed
        self.rng = random.Random(seed)
        self.map_sample = [self.rng.randrange(10) for _ in range(16)]
        self.tick = 0
        self.teams = {t: TeamState() for t in Team}
        self.soldiers = {1: Soldier(1, Team.A, WorldPos(800, 6400)),
                         2: Soldier(2, Team.B, WorldPos(12000, 6400))}
        self.squads = {}
        self.vehicles = {}
        self.facilities = {101: Facility(101, WorldPos(800, 6400), "HQ", Team.A),
                           102: Facility(102, WorldPos(12000, 6400), "HQ", Team.B)}
        self.terrain = alpha_terrain() if self.config.map_width_m == self.config.map_height_m == 128 else Terrain(self.config.map_width_m, self.config.map_height_m)
        self.events = []

    def emit(self, kind, **payload):
        event = dict(event_id=len(self.events), sim_tick=self.tick, event_kind=kind, payload=payload)
        self.events.append(event)
        return event

    def clone(self):
        return deepcopy(self)

    def checksum(self):
        def encode(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            if isinstance(obj, random.Random):
                return obj.getstate()
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            raise TypeError(type(obj))
        data = json.dumps(self.__dict__, default=encode, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return hashlib.sha256(data.encode()).hexdigest()

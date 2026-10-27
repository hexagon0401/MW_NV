from .version import RULES_VERSION,CATALOG_VERSION
"""Versioned JSON checkpoints and command/timing journals, never pickle/eval."""
import json,random
from enum import IntEnum
from . import types
from .config import GameConfig
from .state import WorldState
from .map import Terrain
from .orders import CommandQueue,TeamMap,OrderError
from .runtime import Engine

CLASSES={c.__name__:c for c in (GameConfig,WorldState,Terrain,CommandQueue,TeamMap,types.WorldPos,types.Soldier,types.Squad,types.Vehicle,types.Emplacement,types.Facility,types.TeamState,types.Command)}


def encode(obj):
    if isinstance(obj,IntEnum):return {'enum':type(obj).__name__,'value':int(obj)}
    if isinstance(obj,random.Random):return {'rng':encode(obj.getstate())}
    if isinstance(obj,tuple):return {'tuple':[encode(x) for x in obj]}
    if isinstance(obj,list):return [encode(x) for x in obj]
    if isinstance(obj,dict):return {'dict':[[encode(k),encode(v)] for k,v in obj.items()]}
    if type(obj).__name__ in CLASSES:return {'class':type(obj).__name__,'attrs':encode(vars(obj))}
    if obj is None or type(obj) in (str,int,float,bool):return obj
    raise ValueError('unsupported checkpoint value')


def decode(obj):
    if isinstance(obj,list):return [decode(x) for x in obj]
    if not isinstance(obj,dict):return obj
    if set(obj)=={'enum','value'}:return {'Team':types.Team,'Op':types.Op}[obj['enum']](obj['value'])
    if set(obj)=={'rng'}:
        rng=random.Random();rng.setstate(decode(obj['rng']));return rng
    if set(obj)=={'tuple'}:return tuple(decode(x) for x in obj['tuple'])
    if set(obj)=={'dict'}:return {decode(k):decode(v) for k,v in obj['dict']}
    if set(obj)=={'class','attrs'}:
        c=CLASSES[obj['class']];value=c.__new__(c);vars(value).update(decode(obj['attrs']));return value
    raise ValueError('invalid checkpoint')


class RecordingEngine(Engine):
    def __init__(self,world=None):
        super().__init__(world);self.initial=encode(self.world);self.journal=[]

    def submit(self,command):
        self.journal.append(dict(kind='submit',value=encode(command)))
        return super().submit(command)

    def step(self,dt=.2):
        self.journal.append(dict(kind='step',value=dt))
        return super().step(dt)

    def record_event(self,kind,**payload):
        self.journal.append(dict(kind='event',value=[kind,payload]))
        return self.world.emit(kind,**payload)

    def document(self):
        return dict(version=2,rules_version=self.world.rules_version,catalog_version=self.world.catalog_version,initial=self.initial,journal=self.journal,checksum=self.world.checksum())


def replay(document):
    if document.get('version')!=2 or (document.get('rules_version'),document.get('catalog_version')) not in ((RULES_VERSION,CATALOG_VERSION),('combined-arms-6','combined-arms-3')):raise ValueError('incompatible replay rules/catalog version')
    engine=Engine(decode(document['initial']))
    for action in document['journal']:
        if action['kind']=='submit':
            try:engine.submit(decode(action['value']))
            except OrderError:pass
        elif action['kind']=='step':engine.step(action['value'])
        elif action['kind']=='event':engine.world.emit(action['value'][0],**action['value'][1])
        else:raise ValueError('invalid replay operation')
    if engine.world.checksum()!=document['checksum']:raise ValueError('replay checksum mismatch')
    return engine.world

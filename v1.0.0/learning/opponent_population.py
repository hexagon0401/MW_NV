"""Bounded population/payoff ideas from OpenSpiel; no heldout score ingestion."""
import hashlib,json,random
from pathlib import Path
from .self_play import atomic_json


def select(entries,payoffs,seed,counts=None):
    entries=sorted(entries,key=lambda e:e['id']);counts=counts or {}
    # Six selections per96-game block =25% of24 past-opponent slots.
    available=[e for e in entries if counts.get(e['id'],0)<6] if len(entries)>=4 else entries
    if not available:raise ValueError('opponent block cap exhausted')
    rng=random.Random(seed)
    if rng.random()<.5 or any(payoffs.get(e['id'],{}).get('games',0)<8 for e in available):return rng.choice(available)
    weights=[.05+(1-payoffs[e['id']]['score']/payoffs[e['id']]['games'])**2 for e in available]
    return rng.choices(available,weights=weights,k=1)[0]


def record_payoff(state,policy_id,score,*,partition):
    if partition!='opponent_selection':raise ValueError('heldout evaluation cannot choose training opponents')
    item=state.setdefault('payoffs',{}).setdefault(policy_id,dict(games=0,score=0.))
    item['games']+=1;item['score']+=score


class Population:
    def __init__(self,root):
        self.root=Path(root);self.path=self.root/'population.json'
        self.state=json.loads(self.path.read_text()) if self.path.exists() else dict(entries=[],payoffs={},blocks={})
    def register(self,path,generation,style='unknown',remote=None):
        path=Path(path);digest=hashlib.sha256(path.read_bytes()).hexdigest()
        entry=dict(id=digest,sha256=digest,file=path.name,generation=generation,style=style,remote=remote)
        entries=[e for e in self.state['entries'] if e['id']!=digest]+[entry]
        # Keep earliest, latest, and a deterministic time-spread population.
        entries.sort(key=lambda e:(e['generation'],e['id']))
        if len(entries)>32:
            indices={round(i*(len(entries)-1)/31) for i in range(32)};entries=[e for i,e in enumerate(entries) if i in indices]
        self.state['entries']=entries;self.save();return entry
    def sync_verified(self):
        entries={e['id']:e for e in self.state['entries']}
        for manifest in sorted((self.root/'archive-verified').glob('*.json')):
            m=json.loads(manifest.read_text())
            if m.get('status')!='verified' or m.get('full') or 'transport' not in m:continue
            for member,digest in m.get('policies',{}).items():
                entries.setdefault(digest,dict(id=digest,sha256=digest,file=digest+'.npz',generation=m['generation'],style=m.get('styles',{}).get(member,'unknown'),remote=dict(release=m['release'],transport=m['transport'],member=member)))
        rows=sorted(entries.values(),key=lambda e:(e['generation'],e['id']))
        if len(rows)<=32:self.state['entries']=rows
        else:
            chosen={rows[0]['id']:rows[0],rows[-1]['id']:rows[-1]}
            for style in sorted({e['style'] for e in rows}):
                if len(chosen)>=32:break
                e=next(e for e in reversed(rows) if e['style']==style);chosen[e['id']]=e
            for i in range(32):
                if len(chosen)>=32:break
                e=rows[round(i*(len(rows)-1)/31)];chosen[e['id']]=e
            self.state['entries']=sorted(chosen.values(),key=lambda e:(e['generation'],e['id']))
        self.save()
    def choose(self,episode,learner=None):
        block=str(episode//96);counts=self.state['blocks'].setdefault(block,{})
        available=[e for e in self.state['entries'] if (self.root/'opponents'/e['file']).exists() or e.get('remote')]
        payoffs=self.state.get('payoffs_by_learner',{}).get(learner,self.state['payoffs'])
        e=select(available,payoffs,4903+episode,counts);counts[e['id']]=counts.get(e['id'],0)+1
        self.state['blocks']={block:counts};self.save();return e
    def resolve(self,entry,fetch):
        folder=self.root/'opponents';folder.mkdir(exist_ok=True);path=folder/entry['file']
        if not path.exists():
            if not entry.get('remote'):raise ValueError('opponent unavailable')
            temporary=path.with_suffix('.partial');fetch(entry['remote'],temporary)
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=entry['sha256']:temporary.unlink();raise ValueError('opponent checksum')
            temporary.replace(path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('opponent checksum')
        return path
    def prune(self,pinned=()):
        files=sorted((self.root/'opponents').glob('*.npz'),key=lambda p:p.stat().st_mtime,reverse=True)
        pinned=set(pinned);verified={e['file'] for e in self.state['entries'] if e.get('remote')}
        # Never remove the only unverified copy to pretend the cache limit was met.
        unpinned=[f for f in files if f.name not in pinned]
        keep=pinned|{p.name for p in unpinned[:max(0,8-len(pinned))]}
        for p in files:
            if p.name not in keep and p.name in verified:p.unlink()
        return dict(local=len(list((self.root/'opponents').glob('*.npz'))),blocked_unverified=sum(p.name not in keep and p.name not in verified for p in files))
    def save(self):atomic_json(self.path,self.state)


def fetch_remote(remote,destination):
    import tempfile,tarfile
    from .league_archive import download
    with tempfile.TemporaryDirectory() as tmp:
        archive=download(remote['release'],remote['transport'],tmp)
        with tarfile.open(archive,'r:gz') as tar:
            member=tar.getmember(remote['member'])
            if not member.isfile() or member.size>16*1024**2 or member.name not in ('ppo1.npz','ppo2.npz'):raise ValueError('invalid opponent archive member')
            destination.write_bytes(tar.extractfile(member).read())


def evaluate_selection(root,models,state,progress=None,pinned=()):
    from .mission_policy import export
    from .mission_numpy import NumpyPolicy
    from .mission_evaluate import play
    population=Population(root);population.sync_verified()
    if not population.state['entries']:return
    for i,model in enumerate(models):
        learner=f'PPO{i+1}';scores=population.state.setdefault('payoffs_by_learner',{}).setdefault(learner,{})
        entry=min(population.state['entries'],key=lambda e:(scores.get(e['id'],{}).get('games',0),e['generation'],e['id']))
        opponent=NumpyPolicy(population.resolve(entry,fetch_remote));path=Path(root)/f'probe-ppo{i+1}.npz';export(model,path);policy=NumpyPolicy(path)
        value=dict(games=0,score=0.,source_policy=policy.policy_id,partition='opponent_selection')
        for seed in (9000+state['completed_games']//96*2%900,9001+state['completed_games']//96*2%900):
            for team in (0,1):
                for swap in (False,True):
                    _,result=play(seed,('2','3','4')[(state['completed_games']//96)%3],{team:policy,1-team:opponent},swap,progress,activity_role='evaluation',activity_run=state['run']+'-population')
                    value['games']+=1;value['score']+=.5 if result['winner'] is None else float(result['winner']==team)
        scores[entry['id']]=value;population.save();path.unlink()
    population.prune(pinned)

"""Serialized, recoverable typed apply worker. Public commands never contain argv."""
import argparse,fcntl,json,time
from pathlib import Path
from .releases import Registry
from .release_observations import observe,read


def execute(registry,handlers):
    lock=(registry.root/'apply.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return
    attempt=registry.pending()
    if not attempt:return
    item=registry.get(attempt['release_id'],private=True);definition=read(registry.root/'definitions'/(item['id']+'.json'))
    handler=handlers[item['handler']](definition,registry)
    def save(phase,**values):registry.journal(attempt['id'],phase,**values)
    def journal():
        with registry.db() as c:return json.loads(c.execute('SELECT journal FROM attempts WHERE id=?',(attempt['id'],)).fetchone()[0])
    try:
        if item['content_digest']!=attempt['digest']:raise ValueError('candidate changed')
        if attempt['action']=='rollback':
            with registry.db() as c:old=c.execute("SELECT journal FROM attempts WHERE release_id=? AND phase='APPLIED' ORDER BY updated DESC LIMIT 1",(item['id'],)).fetchone()
            if not old:raise ValueError('rollback source missing')
            save('ROLLING_BACK',rollback_source=json.loads(old[0]));handler.rollback(json.loads(old[0]),lambda **v:save('ROLLING_BACK',**v));save('ROLLED_BACK');return
        if attempt['phase'] in ('RECOVERY_REQUIRED','ROLLING_BACK'):
            handler.rollback(journal(),lambda **v:save('ROLLING_BACK',**v));save('ROLLED_BACK');return
        if attempt['phase']=='QUEUED':
            with registry.db() as c:
                if not all(registry._dependency(c,d) for d in definition['spec']['dependencies']):raise ValueError('release dependencies changed')
            evidence=observe(definition['spec'],definition['paths'],item['content_digest'])
            if evidence.get('evidence_digest')!=item['content_digest'] or evidence.get('blockers') or not set(definition['spec']['validation_plan']).issubset({s['id'] for s in evidence['steps']}) or not all(s['state']=='PASS' for s in evidence['steps'] if s.get('required',True) or s['id'] in definition['spec']['validation_plan']):raise ValueError('required evidence changed')
            handler.validate();save('SAVING')
        phase=registry.pending()['phase']
        if phase=='SAVING':handler.prepare(journal(),lambda **v:save('SAVING',**v));save('SWITCHING')
        if registry.pending()['phase']=='SWITCHING':handler.switch(journal(),lambda **v:save('SWITCHING',**v));save('VERIFYING')
        if registry.pending()['phase']=='VERIFYING':handler.verify(journal());save('APPLIED')
    except Exception as exc:
        with registry.db() as c:registry.event(c,item['id'],'APPLY_FAILED',reason=type(exc).__name__)
        saved=journal()
        try:
            if saved:
                save('ROLLING_BACK');handler.rollback(saved,lambda **v:save('ROLLING_BACK',**v));save('ROLLED_BACK')
            else:save('FAILED')
        except Exception as rollback_error:
            save('RECOVERY_REQUIRED',recovery_reason=type(rollback_error).__name__)

if __name__=='__main__':
    from .release_handlers import MixedTraining,PagesSite
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();execute(Registry(a.root),{'mixed_training':MixedTraining,'pages_site':PagesSite})

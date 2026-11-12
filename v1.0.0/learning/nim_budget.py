"""One cross-process paired request lease, persisted rate limit and fair lane turns."""
import fcntl,json,time
from pathlib import Path

class PairLease:
    def __init__(self,root='data/nim-budget',lane='ordinary'):
        self.root=Path(root);self.lane=lane;self.handle=None;self.admitted=False
    def __enter__(self):
        self.root.mkdir(parents=True,exist_ok=True);self.handle=(self.root/'pair.lock').open('a')
        try:fcntl.flock(self.handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:self.handle.close();self.handle=None;return False
        p=self.root/'state.json'
        try:state=json.loads(p.read_text())
        except (OSError,ValueError):state={}
        now=time.time();pending=self.root/'demonstration-pending';demo_pending=pending.exists() and now-pending.stat().st_mtime<90
        turn=state.get('turn',0)%3
        if now<state.get('next_at',0) or demo_pending and (self.lane=='ordinary')!=(turn==2):return False
        state.update(next_at=now+30,turn=(turn+1)%3,last_lane=self.lane)
        tmp=p.with_suffix('.partial');tmp.write_text(json.dumps(state));tmp.replace(p)
        self.admitted=True;return True
    def defer(self,seconds):
        if not self.admitted:return
        p=self.root/'state.json';state=json.loads(p.read_text());state['next_at']=max(state['next_at'],time.time()+max(0,seconds));p.write_text(json.dumps(state))
    def __exit__(self,*_):
        if self.handle:fcntl.flock(self.handle,fcntl.LOCK_UN);self.handle.close()

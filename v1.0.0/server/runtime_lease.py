"""Single-host lease admission. No inference, game RNG or remote commands here."""
import hashlib,hmac,json,os,time,uuid,re
from pathlib import Path
from urllib.request import Request,urlopen
from .telemetry import atomic

def boot_id():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()

def lease_valid(root,base=None,now=None,boot=None):
    base=Path(base or os.environ.get('MW_NV_INSTALLATION_BASE',Path(__file__).resolve().parents[1]));config=base/'data/runtime/config.json'
    if not config.exists():return True
    try:
        spec=json.loads(config.read_text())
        if Path(spec['root']).resolve()!=Path(root).resolve():return not Path(root).resolve().is_relative_to(base/'data/releases/production')
        row=json.loads((base/'data/runtime/lease.json').read_text())
        return row['boot_id']==(boot or boot_id()) and row['root']==str(Path(root).resolve()) and row['deadline']>(time.monotonic() if now is None else now)
    except (OSError,ValueError,KeyError):return False

class Client:
    def __init__(self,base,config,opener=urlopen):
        if not re.fullmatch(r'https://[a-z0-9.-]+\.workers\.dev/?',config['monitor_url']):raise ValueError('registered monitor URL required')
        self.base=Path(base);self.config=config;self.opener=opener;path=self.base/'data/runtime/instance.json';self.boot=boot_id()
        try:old=json.loads(path.read_text())
        except (OSError,ValueError):old={}
        self.instance=old.get('instance_id') if old.get('boot_id')==self.boot else str(uuid.uuid4())
        atomic(path,dict(boot_id=self.boot,instance_id=self.instance))
    def send(self,action,run_id,health):
        start=time.monotonic();stamp=str(int(time.time()));nonce=str(uuid.uuid4())
        key=Path(self.config['key_file']).read_text().strip()
        body=json.dumps(dict(action=action,instance_id=self.instance,boot_id=self.boot,run_id=run_id,health=health),separators=(',',':')).encode()
        signature=hmac.new(key.encode(),stamp.encode()+b'\n'+nonce.encode()+b'\n'+body,hashlib.sha256).hexdigest()
        req=Request(self.config['monitor_url'].rstrip('/')+'/lease',data=body,method='POST',headers={'Content-Type':'application/json','X-Runtime-Time':stamp,'X-Runtime-Request':nonce,'X-Runtime-Signature':signature})
        with self.opener(req,timeout=10) as response:reply=json.load(response)
        if not reply.get('granted'):raise ValueError('lease denied')
        seconds=max(0,min(165,reply['lease_until']-reply['server_time']-15))
        atomic(self.base/'data/runtime/lease.json',dict(boot_id=self.boot,instance_id=self.instance,root=self.config['root'],deadline=start+seconds))
        return seconds>0


def hourly_backup_due(state,now=None):
    return (time.time() if now is None else now)-state.get("last_full_request_at",0)>=3600

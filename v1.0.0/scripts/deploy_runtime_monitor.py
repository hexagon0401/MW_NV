"""Explicit free-plan deployment. Fails before creating resources when D1 auth is missing."""
import argparse,json,os,re,subprocess,secrets,urllib.request
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
ACCOUNT='6974fa0dd5aeb87d1c8a95cd4e85e27d'
def api(path,method='GET',body=None):
    req=urllib.request.Request('https://api.cloudflare.com/client/v4/accounts/'+ACCOUNT+path,method=method,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['CLOUDFLARE_API_TOKEN'],'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:d=json.load(response)
    if not d.get('success'):raise ValueError('Cloudflare request failed')
    return d['result']

def main():
    p=argparse.ArgumentParser();p.add_argument('--confirm-free',action='store_true',help='Use only after account UI/API confirms Workers Free');a=p.parse_args()
    if not a.confirm_free:raise SystemExit('Workers Free confirmation required; no resources changed')
    # Read permission probe precedes any create/update.
    databases=api('/d1/database');database=next((d for d in databases if d['name']=='mw-nv-runtime'),None)
    if database is None:database=api('/d1/database','POST',dict(name='mw-nv-runtime'))
    ident=database['uuid'];sql=(BASE/'cloud/runtime-monitor/schema.sql').read_text()
    for statement in sql.split(';'):
        if statement.strip():api('/d1/database/'+ident+'/query','POST',dict(sql=statement))
    folder=BASE/'data/runtime';folder.mkdir(exist_ok=True);key=folder/'monitor.key'
    if not key.exists():key.write_text(secrets.token_hex(32));key.chmod(0o600)
    config=dict(name='mw-nv-runtime-monitor',main=str(BASE/'cloud/runtime-monitor/index.js'),compatibility_date='2026-11-04',workers_dev=True,triggers=dict(crons=['*/5 * * * *']),d1_databases=[dict(binding='DB',database_name='mw-nv-runtime',database_id=ident)])
    path=folder/'monitor-wrangler.json';path.write_text(json.dumps(config));cli=BASE/'viewer/node_modules/.bin/wrangler';env=dict(os.environ,WRANGLER_LOG_PATH='/tmp/mw-runtime-deploy')
    result=subprocess.run([str(cli),'deploy','--config',str(path)],env=env,capture_output=True,text=True,check=True)
    subprocess.run([str(cli),'secret','put','RUNTIME_HMAC_KEY','--config',str(path)],input=key.read_text(),env=env,capture_output=True,text=True,check=True)
    urls=re.findall(r'https://[a-z0-9.-]+\.workers\.dev',result.stdout)
    if not urls:raise ValueError('deployed URL missing')
    (folder/'monitor-deployment.json').write_text(json.dumps(dict(url=urls[-1],database_id=ident,free_confirmed=True,key_file=str(key))))
    print('Monitor deployed:',urls[-1]);print('Persist monitor.key into Codex secret MW_NV_RUNTIME_MONITOR_KEY; never paste it into chat.')
if __name__=='__main__':main()

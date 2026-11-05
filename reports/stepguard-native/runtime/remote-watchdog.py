"""Only the provider-injected pod-scoped key is used. Never log its value."""
import json,os,time,urllib.request,sys
from pathlib import Path
injected=dict(x.split(b'=',1) for x in Path('/proc/1/environ').read_bytes().split(b'\0') if b'=' in x)
pod=injected[b'RUNPOD_POD_ID'].decode();key=injected[b'RUNPOD_API_KEY'].decode()
deadline=float(sys.argv[1]);base='https://api.runpod.io/v2/pods/'+pod
def api(method,suffix='',body=None):
    req=urllib.request.Request(base+suffix,method=method,data=json.dumps(body).encode() if body else None,
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:return r.status
# Read-only proof that the injected credential can address its own pod.
status=api('GET')
Path('/root/watchdog-ready.json').write_text(json.dumps({'ready':True,'own_pod_read_status':status,'deadline_epoch':deadline,'pid':os.getpid()}))
while time.time()<deadline:time.sleep(min(30,deadline-time.time()))
for i in range(30):
    try:api('POST','/action',{'action':'stop'});break
    except Exception as exc:print(type(exc).__name__,flush=True);time.sleep(5)

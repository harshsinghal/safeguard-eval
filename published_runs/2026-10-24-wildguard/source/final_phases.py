import subprocess
for phase in ('holdout','expanded'):
 with open('/root/'+phase+'-phase.log','w') as log:
  subprocess.run(['python3','/root/serve_and_run.py','--jobs','/root/'+phase+'-jobs.json'],stdout=log,stderr=subprocess.STDOUT,check=True)
print('FINAL PHASES COMPLETE',flush=True)

"""Ready-gated invocation of an unchanged native CLI. No search implementation."""
import json,subprocess,sys,time
from pathlib import Path
def oom_kills():
 try:return int(dict(line.split() for line in Path("/sys/fs/cgroup/memory.events").read_text().splitlines()).get("oom_kill",0))
 except OSError:return 0
system=sys.argv[1]
commands={
 'S01':['/opt/synthphonia/target/release/synthphonia','-j','2','/case/task.sl'],
 'S02':['/artifact/synth/build/merlin','--input-file=/case/task.sl','--check-violation','1','--cutoff-size','3','--n-values-check','3','--reuse-components','1','--use-oe','1','--max-contexts','1','--domain=string','--silent','1']}
def emit(r):print(json.dumps(r,ensure_ascii=False),flush=True)
emit({'event':'ready','system':system,'model_loaded':False})
for line in sys.stdin:
 r=json.loads(line);start=time.monotonic()
 try:
  # Native stderr is streamed directly to the host, including a panic or OOM symptom.
  before=oom_kills()
  p=subprocess.run(commands[system],stdout=subprocess.PIPE,timeout=r['timeout_seconds'])
  emit({'event':'search_complete','task_id':r['task_id']})
  emit({'task_id':r['task_id'],'status':'native_result','native_exit_code':p.returncode,'native_oom_kill_delta':oom_kills()-before,'native_stdout':p.stdout.decode('utf-8','replace'),'native_seconds':time.monotonic()-start})
 except subprocess.TimeoutExpired:
  emit({'event':'search_complete','task_id':r['task_id']})
  emit({'task_id':r['task_id'],'status':'search_timeout','native_seconds':time.monotonic()-start})
 except Exception as e:
  emit({'task_id':r['task_id'],'status':'adapter_error','message':str(e)})

import json,sys
from crossbeam_adapter import native_run
for line in sys.stdin:
 r=json.loads(line)
 try:result={'task_id':r['task_id'],'status':'executed','outputs':[native_run(r['expression'],x) for x in r['inputs']]}
 except Exception as e:result={'task_id':r['task_id'],'status':'execution_error','message':str(e)}
 print(json.dumps(result,ensure_ascii=False),flush=True)

from pbe.assessment import assess, export, identity
from .common import ROOT, read, write, rows, cases


def profile(args):
    programs=read(ROOT/'records/main_programs.json')
    record=next((p for p in programs if (p['condition'],p['repeat'],p['task_id'])==
                 (args.condition,args.repeat,args.task)),None)
    if record is None:
        raise ValueError('No frozen program for this condition, repetition and task.')
    cfg=read(ROOT/'experiments/main.json')
    cfg.update(systems=[record['system']],task_ids=[args.task],
               study_run=dict(condition=args.condition,repeat=args.repeat))
    metadata=identity(cfg,record['system'])
    predictions,bases=[],[]
    definitions={(c['suite'],c['case_id']):c for c in cases('main',args.task)}
    for row in rows(ROOT/'records/main.jsonl.gz'):
        if row['program_id']!=record['id']:
            continue
        case=definitions[row['suite'],row['case_id']]
        item=dict(**metadata,task_id=args.task,input=case['input'],expected=case['expected'],
                  status=row['status'],actual=row['actual'])
        if row['suite']=='training':
            bases.append(dict(item,base_id=row['case_id']))
        else:
            predictions.append(dict(item,suite=row['suite'],case_id=row['case_id']))
    record=dict(record,study_run=cfg['study_run'],run_id=cfg.get('run_id'))
    result=assess(ROOT,cfg,predictions,bases,{record['system']+'/'+args.task:record})
    args.output.mkdir(parents=True,exist_ok=False)
    export(args.output,result)
    write(args.output/'program.json',record)
    print('Profile, check outcomes and applicability exported for',record['id'])

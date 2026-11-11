from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import fcntl
import gzip
import json
import os
from uuid import uuid4

from pbe.evaluation import prepare_candidate, engine_for, execute_checked
from pbe.io import verified_program
from pbe.runtime import ensure
from pbe.assessment import INFRASTRUCTURE
from .common import ROOT, read, write, sha, task, cases, observations, passed, table
from .programs import collect


def evaluate(args):
    index='main' if args.suite=='random' else args.suite
    programs, synthesis = collect(args.programs, args.suite) if args.programs else (read(ROOT/'records'/(index+'_programs.json')), None)
    allowed=set(read(ROOT/'data/cohort.json')['task_ids']) if args.suite in ['random','selection'] else None
    programs=[p for p in programs if (allowed is None or p['task_id'] in allowed)
              and (not args.task or p['task_id']==args.task)
              and (not args.system or p['system']==args.system)]
    if not programs or args.workers<1:
        raise ValueError('Choose a nonempty program set and a positive worker count.')
    out=args.output.resolve()
    if out.is_relative_to(ROOT/'data') or out.is_relative_to(ROOT/'records'):
        raise ValueError('Choose a separate output directory.')
    out.mkdir(parents=True,exist_ok=True)
    lock=(out/(args.suite+'.lock')).open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    manifest_path=out/(args.suite+'_execution.json')
    manifest=dict(suite=args.suite,programs=[p['id'] for p in programs],
                  program_hashes={p['id']:p['sha256'] for p in programs},
                  cases={t:cases(args.suite,t) for t in sorted({p['task_id'] for p in programs})})
    if args.programs:
        manifest.update(mode='new', program_index=programs, synthesis=synthesis)
    if manifest_path.exists():
        if not args.resume or read(manifest_path)!=manifest:
            raise ValueError('Use a fresh output directory or resume the identical run.')
    else:
        write(manifest_path,manifest)
    if args.programs:
        write(out/(args.suite+'_programs.json'), programs)
    images=ensure(ROOT,sorted({p['system'] for p in programs}))
    selected_ids={p['id'] for p in programs}
    reference={} if args.programs else {key:row for key,row in observations(args.suite).items() if key[0] in selected_ids}

    def run(program):
        pid,tid=program['id'],program['task_id']
        folder=out/'execution'/args.suite/pid
        receipt=folder/'complete.json'
        target=folder/'observations.jsonl'
        if receipt.exists():
            done=read(receipt)
            if done['sha256']!=sha(target):
                raise ValueError('Changed completed observations.')
            return pid
        if folder.exists():
            raise ValueError('An incomplete execution requires inspection. Choose a fresh output directory.')
        folder.mkdir(parents=True)
        rec={**program,'path':str(ROOT/program['path'])}
        if sha(rec['path'])!=rec['sha256']:
            raise ValueError('Changed program.')
        prepare_candidate(ROOT,rec,folder)
        value=verified_program(ROOT,rec)
        engine=None
        try:
            engine=engine_for(ROOT,rec,folder,image=images[rec['system']])
            data=task(tid)
            examples=(data['split']['training']+data['split']['heldout'])[:program['examples']]
            for i,example in enumerate(examples):
                result=execute_checked(engine,rec,value,f'training-{i}',example['input'])
                if result['status']!='returned' or result['actual']!=example['output']:
                    raise ValueError('A frozen program no longer passes its demonstrations.')
            with target.open('w') as stream:
                for case in manifest['cases'][tid]:
                    if engine.closed:
                        engine=engine_for(ROOT,rec,folder,image=images[rec['system']])
                    result=execute_checked(engine,rec,value,case['case_id'],case['input'])
                    if result['status'] in INFRASTRUCTURE:
                        raise RuntimeError('Runtime infrastructure failure.')
                    row=dict(program_id=pid,case_id=case['case_id'],suite=case['suite'],status=result['status'],actual=result['actual'])
                    old=reference.get((pid,case['suite'],case['case_id']))
                    if old and (row['status'],row['actual'])!=(old['status'],old['actual']):
                        write(folder/'mismatch.json',dict(case=case,expected=old,observed=row))
                        raise ValueError('Output differs from the recorded execution.')
                    stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
            write(receipt,dict(program_sha256=rec['sha256'],sha256=sha(target),cases=len(manifest['cases'][tid])))
        finally:
            if engine is not None:
                engine.close()
        return pid

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run,p) for p in programs]
        for i,future in enumerate(as_completed(futures),1):
            future.result()
            if i%20==0 or i==len(futures):
                print(f'{args.suite}: {i}/{len(futures)} programs.',flush=True)
    target=out/(args.suite+'.jsonl.gz')
    temp=target.with_name(target.name+'.'+uuid4().hex+'.tmp')
    with gzip.open(temp,'wt') as stream:
        for p in programs:
            stream.write((out/'execution'/args.suite/p['id']/'observations.jsonl').read_text())
    temp.replace(target)
    if args.programs:
        metrics=[]
        for p in programs:
            totals=defaultdict(lambda: [0,0])
            expected={(c['suite'],c['case_id']):c['expected'] for c in manifest['cases'][p['task_id']]}
            for line in (out/'execution'/args.suite/p['id']/'observations.jsonl').read_text().splitlines():
                row=json.loads(line)
                totals[row['suite']][0]+=passed(row,expected[row['suite'],row['case_id']])
                totals[row['suite']][1]+=1
            for suite,(ok,total) in totals.items():
                metrics.append(dict(program_id=p['id'],task_id=p['task_id'],suite=suite,passed=ok,total=total,accuracy=ok/total))
        table(out/(args.suite+'_task_metrics.csv'),metrics)
    receipt=dict(programs=len(programs),outputs_match_reference=None if args.programs else True,observations_sha256=sha(target))
    if args.programs:
        receipt['program_index_sha256']=sha(out/(args.suite+'_programs.json'))
    write(out/(args.suite+'_validation.json'),receipt)
    lock.close()

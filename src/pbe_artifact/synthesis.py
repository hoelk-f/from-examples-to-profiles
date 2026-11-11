from pathlib import Path
import shutil

from pbe.runtime import CLASSIC, ensure
from pbe.provider import Provider
from pbe.systems import dsl
from pbe.systems.direct import direct
from pbe.systems.hysynth.common import digest, encoded
from pbe.systems.hysynth.process_pool import check_pool
from .common import ROOT, ORDER, read, write, sha, task
from .python_format import extract


def prepare_hysynth(tid, n, suite, pool_path, live=False):
    folders = [ROOT/'artifacts/llm/dsl/tasks'/tid]
    plans = [ROOT/'artifacts/llm/dsl/live-plan.json', ROOT/'artifacts/llm/dsl/plan.json']
    if suite == 'sensitivity':
        folders.insert(0, ROOT/f'data/synthesis/sensitivity/prepared/n{n}'/tid)
        plans.insert(0, ROOT/f'data/synthesis/sensitivity/plans/n{n}.json')
    pool = None if live else read(pool_path)
    for folder in folders:
        meta = read(folder/'task.json')
        for path in plans:
            plan = read(path)
            if pool and (meta['task_id'] != pool['task_id'] or
                         meta['request_sha256'] != pool['request_sha256'] or
                         meta['training_sha256'] != pool['training_sha256'] or
                         digest(encoded(plan)) != pool['plan_sha256']):
                continue
            if pool:
                check_pool(pool, meta, plan)
            examples = (task(tid)['split']['training']+task(tid)['split']['heldout'])[:n]
            if read(folder/'training.json')['examples'] != examples:
                raise ValueError('Prepared training examples differ.')
            return dict(taskdir=folder, task=meta, plan=plan,
                        messages=read(folder/'request.json')['messages'], pool=pool_path)
    raise ValueError('Recorded proposal pool has no matching preparation.')


def synthesize(args):
    if args.condition not in ORDER:
        raise ValueError('Condition must be one of: '+', '.join(ORDER))
    system, _, slot = args.condition.partition('/')
    max_repeat = 1 if not slot else 3 if args.suite == 'sensitivity' and system == 'hysynth-string' else 5
    if not 1 <= args.repeat <= max_repeat or args.suite == 'main' and args.examples != 2:
        raise ValueError('Repetition or example count is outside the study design.')
    tids = read(ROOT/'data/selection.json')['selected_tasks'] if args.suite == 'main' else read(ROOT/'data/sensitivity/protocol.json')['task_ids']
    if args.task:
        if args.task not in tids:
            raise ValueError('Task is outside the selected experiment.')
        tids = [args.task]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=args.resume)
    images = ensure(ROOT, [system], synthesis=True)
    provider = None
    if args.live:
        if not slot or not args.provider:
            raise ValueError('Live model requests require an LLM condition and --provider.')
        config = read(args.provider)[slot]
        provider = Provider(config, len(tids)*(10 if system == 'hysynth-string' else 1), out/'request-ledger.json')
    elif args.provider:
        raise ValueError('--provider requires explicit --live.')
    protocol = dict(suite=args.suite, condition=args.condition,
          repeat=args.repeat, examples=args.examples, task_ids=tids,
          response_mode='live' if args.live else 'recorded', images=images)
    if (out/'protocol.json').exists() and read(out/'protocol.json') != protocol:
        raise ValueError('Existing synthesis uses a different protocol.')
    write(out/'protocol.json', protocol)
    programs, outcomes = [], []
    for tid in tids:
        n = args.examples
        examples = [{k: e[k] for k in ['input','output']}
                    for e in (task(tid)['split']['training']+task(tid)['split']['heldout'])[:n]]
        folder = out/tid
        grammar = None
        if (folder/'result.json').exists():
            result = read(folder/'result.json')
            where = folder/'dsl/processed/hysynth' if system == 'hysynth-string' else folder
            grammar = folder/'task.native.sl' if system == 'hysynth-string' and result.get('frozen') else None
        elif folder.exists():
            raise ValueError('An unfinished individual synthesis requires inspection: '+str(folder))
        elif system in CLASSIC:
            if args.suite == 'sensitivity':
                from .sensitivity_classical import run_one
            else:
                from pbe.systems.synthesis import run_one
            result = run_one(CLASSIC[system], dict(task_id=tid, examples=examples), folder)
            where = folder
        else:
            path = ROOT/'data/synthesis'/args.suite/system/slot
            if args.suite == 'sensitivity':
                path = path/f'n{n}'
            path = path/f'repeat-{args.repeat}'/(tid+'.json')
            folder.mkdir()
            if system == 'direct-python':
                recorded = read(path)
                write(folder/'request.json', dict(messages=recorded['messages']))
                answer = provider.complete(recorded['messages'], folder/'request')['text'] if provider else recorded['text']
                code, rule = extract(answer)
                (folder/'response.txt').write_text(answer)
                write(folder/'format.json', rule)
                result = direct(read(ROOT/'runtimes/legacy/configuration.json'), folder, code, examples)
                where = folder
            else:
                prep = prepare_hysynth(tid, n, args.suite, path, args.live)
                result, where = dsl.run(prep, [system], folder/'dsl', folder/'pool.json',
                                        provider, images=images)[system]
                grammar = prep['taskdir']/'task.native.sl'
        write(folder/'result.json', result)
        outcomes.append(dict(task_id=tid, status=result['status'], frozen=result.get('frozen', False)))
        if result.get('frozen'):
            program = where/result['program_file']
            if sha(program) != result['program_sha256']:
                raise ValueError('Synthesized program hash differs from its completion record.')
            record = dict(id=args.condition.replace('/','__')+f'__r{args.repeat}__n{n}__{tid}',
                          condition=args.condition, repeat=args.repeat, examples=n, task_id=tid,
                          system=system, runtime=system, path=str(program), sha256=sha(program))
            if grammar:
                target = folder/'task.native.sl'
                if grammar != target:
                    shutil.copy2(grammar, target)
                record.update(grammar=str(target), grammar_sha256=sha(target))
            programs.append(record)
        write(out/'programs.json', programs)
        write(out/'outcomes.json', outcomes)
        print(tid, result['status'], flush=True)

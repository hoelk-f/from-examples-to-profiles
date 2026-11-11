from pathlib import Path
import shutil
from pbe.io import read, write, check_reference
from pbe.checkpoint import retain
from .hysynth.common import AdapterError, digest, encoded, sha, task_parts
from .hysynth.process_pool import check_pool, process
from .hysynth.smt_transport import String


SYSTEMS = {'direct-dsl', 'hysynth-string'}
ARMS = {'direct-dsl': 'direct_dsl', 'hysynth-string': 'hysynth'}


def prepared(root, cfg, task_id, examples, pool_dir=None, live=False):
    spec = cfg.get('dsl')
    if not spec:
        raise ValueError('Choose --experiment llm-dsl or llm-dsl-pilot for DSL synthesis.')
    taskdir = root / spec['tasks'] / task_id
    for name in ['task.json', 'training.json', 'request.json', 'task.standard.sl', 'task.native.sl']:
        check_reference(root, taskdir/name)
    plan_path = root/spec.get('live_plan',spec['plan']) if live else root/spec['plan']
    check_reference(root, plan_path)
    task = read(taskdir/'task.json')
    plan = read(plan_path)
    if type(plan.get('attempts_per_task')) is not int or plan['attempts_per_task'] < 1:
        raise ValueError('The DSL plan needs a positive proposal count.')
    for key, name in [('training_sha256','training.json'), ('request_sha256','request.json'),
                      ('grammar_sha256','task.standard.sl'), ('native_grammar_sha256','task.native.sl')]:
        if sha(taskdir/name) != task[key]:
            raise AdapterError('Prepared synthesis input changed: '+name)
    if read(taskdir/'training.json')['examples'] != examples:
        raise AdapterError('Prepared DSL examples differ from the experiment split.')
    grammar = (taskdir/'task.standard.sl').read_text(encoding='utf-8')
    forms, _ = task_parts(grammar)
    constraints = [f for f in forms if isinstance(f,list) and f and f[0]=='constraint']
    expected = [['constraint',['=',['f',String(e['input'])],String(e['output'])]] for e in examples]
    if constraints != expected:
        raise AdapterError('Grammar constraints differ from the synthesis examples.')
    request = read(taskdir/'request.json')['messages']
    if len(request) != 2 or request[0]['role'] != 'system' or request[1] != {
        'role':'user', 'content':'Synthesize f(x). The grammar and both examples are:\n\n'+grammar}:
        raise AdapterError('Prepared request does not match the DSL grammar.')
    source = Path(pool_dir)/f'{task_id}.json' if pool_dir else root/spec['pools']/f'{task_id}.json'
    if not live:
        if not source.is_file():
            raise ValueError(f'No recorded DSL pool for {task_id}. Use llm-dsl-pilot, --pool-dir DIR, or explicit --live --provider CONFIG.json.')
        check_reference(root, source)
        pool = read(source)
        if pool.get('plan_sha256') != digest(encoded(plan)) and spec.get('live_plan'):
            check_reference(root, root/spec['live_plan'])
            plan = read(root/spec['live_plan'])
        check_pool(pool,task,plan)
    return {'taskdir':taskdir,'task':task,'plan':plan,'messages':request,'pool':source}


def collect(prep, provider, folder):
    config = provider.config
    collection = {'provider':config['endpoint'],'model':config['model'],
        'generation_parameters':{k:config[k] for k in ['temperature','top_p','seed','max_tokens','timeout_seconds','provider','reasoning_effort','think'] if k in config},
        'separate_requests_per_sample':True,'completions_per_request':1,
        'provider_fallback_allowed':False,'model_fallback_allowed':False}
    task = prep['task']
    pool = {'schema_version':1,'task_id':task['task_id'],
        **{k:task[k] for k in ['request_sha256','training_sha256','grammar_sha256']},
        'plan_sha256':digest(encoded(prep['plan'])),'origin':'independent_model_requests',
        'model':config['model'],'provider':config['endpoint'],'collection_configuration':collection,
        'collection_configuration_sha256':digest(encoded(collection)),'samples':[]}
    if (folder / 'pool.json').exists():
        previous = read(folder / 'pool.json')
        if {**previous, 'samples': []} != pool:
            raise AdapterError('Partial response pool identity changed')
    else:
        previous = {**pool, 'samples': []}
        write(folder / 'pool.json', pool)
    for i in range(prep['plan']['attempts_per_task']):
        response = provider.complete(prep['messages'],folder/f'sample-{i:03}')
        pool['samples'].append({'sample_id':i,'status':'completed','text':response['text'],
            'request_id':response['request_id'],'usage':response['usage'],
            'returned_model':response.get('returned_model'),'provider_response_id':response.get('provider_response_id')})
        saved_samples = previous['samples']
        if i < len(saved_samples) and pool['samples'][i] != saved_samples[i]:
            raise AdapterError('Saved pool sample differs from its preserved request')
        if len(pool['samples']) > len(saved_samples):
            write(folder/'pool.json',pool)
    check_pool(pool,task,prep['plan'])
    return folder/'pool.json'


def run(prep, systems, folder, pool_target, provider=None, images=None, resume=False):
    source = collect(prep,provider,folder/'requests') if provider else prep['pool']
    pool_target.parent.mkdir(parents=True,exist_ok=True)
    if pool_target.exists():
        if pool_target.read_bytes() != source.read_bytes():
            raise AdapterError('Sealed pool differs from recorded requests')
    else:
        shutil.copy2(source,pool_target)
    processed = folder/'processed'
    result = process(prep['taskdir'],pool_target,processed,prep['plan'],arms=systems, **({'images': images, 'resume': resume} if images or resume else {}))
    return {system:(result[ARMS[system]],processed/ARMS[system]) for system in systems}

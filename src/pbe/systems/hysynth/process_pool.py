"""Consume one sealed response pool for both DSL arms. No API calls."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
from .common import ROOT, AdapterError, read, save, sha, digest, encoded, classify, validate_final, require_aligned_grammar, verify_seal
from . import runtime
from pbe.checkpoint import retain


def check_pool(pool, task, plan, control=False):
    if pool.get('schema_version') != 1 or pool.get('task_id') != task['task_id']:
        raise AdapterError('Wrong response-pool schema or task')
    for key in ['request_sha256', 'training_sha256', 'grammar_sha256']:
        if pool.get(key) != task[key]:
            raise AdapterError('Pool does not match the prepared '+key)
    if pool.get('plan_sha256') != digest(encoded(plan)):
        raise AdapterError('Pool does not match the chosen proposal budget')
    if not isinstance(pool.get('model'), str) or not pool['model']:
        raise AdapterError('Model identity required')
    expected_origin = 'synthetic_control' if control else 'independent_model_requests'
    if pool.get('origin') != expected_origin:
        raise AdapterError('Response origin does not match processing mode')
    samples = pool.get('samples')
    if not isinstance(samples, list) or len(samples) != plan['attempts_per_task']:
        raise AdapterError('Incomplete pool or unexpected number of attempts')
    if [s.get('sample_id') for s in samples] != list(range(len(samples))):
        raise AdapterError('Sample IDs must be ordered and contiguous, starting at zero')
    if any(s.get('status') not in ['completed', 'request_error'] for s in samples):
        raise AdapterError('Unknown request status')
    if any(s.get('status') != 'completed' for s in samples):
        raise AdapterError('Transport-incomplete pool. Preserve and review without replacement requests.')
    if not all(isinstance(s.get('text'), str) for s in samples):
        raise AdapterError('All raw completion texts must be preserved')
    if not control:
        if not isinstance(pool.get('provider'), str) or not pool['provider']:
            raise AdapterError('Provider identity required')
        collection = pool.get('collection_configuration')
        if not isinstance(collection, dict) or not isinstance(collection.get('generation_parameters'), dict):
            raise AdapterError('Frozen collection configuration including generation parameters required')
        if collection.get('provider') != pool['provider'] or collection.get('model') != pool['model']:
            raise AdapterError('Collection configuration identity mismatch')
        if pool.get('collection_configuration_sha256') != digest(encoded(collection)):
            raise AdapterError('Collection configuration hash mismatch')
        if collection.get('separate_requests_per_sample') is not True or collection.get('completions_per_request') != 1:
            raise AdapterError('One completion in each separate request required')
        if collection.get('provider_fallback_allowed') is not False:
            raise AdapterError('Provider fallback must be explicitly disabled')
        identities = [s.get('request_id') for s in samples]
        if any(not isinstance(x, str) or not x for x in identities) or len(set(identities)) != len(identities):
            raise AdapterError('Distinct recorded request IDs required. Copying a response is not independent sampling.')
        if any(not isinstance(s.get('usage'), dict) for s in samples):
            raise AdapterError('Usage records required for each request')
    return samples


def first_consistent(rows):
    return next((r for r in rows if r['status'] == 'valid' and r['training_consistent']), None)


def freeze(expression, grammar, expected, case, folder, pool_sha, arm, sample_id=None, images=None, resume=False):
    # This gate runs before any candidate file can be frozen.
    checked = validate_final(expression, grammar)
    if resume and (folder / 'result.json').exists():
        saved = read(folder / 'result.json')
        if saved.get('pool_sha256') != pool_sha or sha(folder / saved['program_file']) != saved['program_sha256']:
            raise AdapterError('Frozen native checkpoint changed')
        return saved
    checks = []
    for repeat in range(2):
        result = runtime.inspect_pool(case, folder/f'replay_{repeat}', [{'sample_id': 0, 'expression': checked}], **({'images': images, 'resume': resume} if images or resume else {}))[0]
        passed = result['status'] == 'returned' and result['outputs'] == expected
        checks.append({'outputs': result.get('outputs'), 'expected': expected, 'pass': passed})
        if not passed:
            raise AdapterError('Candidate failed independent training replay before freezing')
    data = checked.encode('utf-8')
    folder.mkdir(parents=True, exist_ok=True)
    program = folder / 'program.native.expr'
    if program.exists():
        if program.read_bytes() != data:
            raise AdapterError('Existing frozen candidate differs')
    else:
        program.write_bytes(data)
    record = {'status': 'frozen', 'frozen': True, 'arm': arm, 'pool_sha256': pool_sha,
              'program_file': 'program.native.expr', 'program_sha256': digest(data), 'checks': checks,
              'final_grammar_validated': True, 'source_sample_id': sample_id}
    save(folder/'result.json', record)
    return record


def process(taskdir, pool_path, out, plan, control=False, arms=('direct-dsl', 'hysynth-string'), images=None, resume=False):
    if not arms or set(arms) - {'direct-dsl', 'hysynth-string'}:
        raise AdapterError('Unknown DSL arm')
    taskdir, pool_path, out = Path(taskdir), Path(pool_path), Path(out)
    if out.exists() and not resume:
        raise FileExistsError('Use a fresh output directory')
    for key in ['search_seconds', 'search_wall_seconds']:
        if key in plan and plan[key] != read(ROOT/'runtime.json')[key]:
            raise AdapterError('Search budget differs from the recorded plan')
    task = read(taskdir/'task.json')
    for field, filename in [('training_sha256', 'training.json'), ('grammar_sha256', 'task.standard.sl'),
                             ('native_grammar_sha256', 'task.native.sl'), ('request_sha256', 'request.json')]:
        if sha(taskdir/filename) != task[field]:
            raise AdapterError('Prepared task changed: '+filename)
    grammar = (taskdir/'task.standard.sl').read_text(encoding='utf-8')
    count = len(read(taskdir/'training.json')['examples'])
    if not 1 <= count <= 5 or require_aligned_grammar(grammar) != count:
        raise AdapterError('One to five matching synthesis examples required')
    expected = [r['output'] for r in read(taskdir/'training.json')['examples']]
    raw = pool_path.read_bytes()
    pool = read(pool_path)
    out.mkdir(parents=True, exist_ok=resume)
    if images or resume:
        retain(out / 'identity.json', {'task': task, 'pool_sha256': sha(pool_path), 'plan': plan,
            'arms': list(arms), 'images': images, 'control': control})
    if (out / 'result.json').exists():
        if (out / 'SHA256SUMS.json').exists():
            verify_seal(out, 'SHA256SUMS.json')
        else:
            raise AdapterError('Finished native result has no seal. Inspect the preserved result before resuming.')
        return read(out / 'result.json')
    if (out / 'raw_pool.json').exists():
        if (out / 'raw_pool.json').read_bytes() != raw:
            raise AdapterError('Saved pool changed')
    else:
        (out / 'raw_pool.json').write_bytes(raw)
    retain(out / 'plan.json', plan)
    case = out/'execution'
    case.mkdir(exist_ok=resume)
    shutil.copy2(taskdir/'task.native.sl', case/'task.sl')
    try:
        samples = check_pool(pool, task, plan, control)
        rows = [{'sample_id': s['sample_id'], 'raw_text_sha256': digest(s['text'].encode('utf-8')),
                 **classify(s['text'], grammar)} for s in samples]
        save(out/'proposal_validation.json', rows)
        parseable = [r for r in rows if r['status'] == 'grammar_valid']
        if parseable:
            native = runtime.inspect_pool(case, out/'native_qualification', [
                {'sample_id': r['sample_id'], 'expression': r['native_expression']} for r in parseable], **({'images': images, 'resume': resume} if images or resume else {}))
            save(out/'native_qualification.json', native)
            for row, checked in zip(parseable, native):
                if checked['status'] != 'returned':
                    row.update(status='native_error', native_error=checked)
                    save(out/'proposal_validation.json', rows)
                    raise AdapterError('A grammar-conforming proposal failed in the native interpreter. Review the adapter before proceeding.')
                row.update(status='valid', training_outputs=checked['outputs'], training_consistent=checked['outputs'] == expected)
        save(out/'proposal_validation.json', rows)
        valid = [r for r in rows if r['status'] == 'valid']
        # Do not deduplicate. Repeated independently generated answers carry frequency.
        expressions = [r['native_expression'] for r in valid]
        save(case/'completions.json', {'task.sl': {'solutions': expressions}})
        selected = first_consistent(rows)
        direct = {'status': 'no_training_consistent_proposal', 'frozen': False}
        if selected is not None and 'direct-dsl' in arms:
            direct = freeze(selected['native_expression'], grammar, expected, case, out/'direct_dsl', sha(out/'raw_pool.json'), 'direct_dsl', selected['sample_id'], images=images, resume=resume)
        guided = {'status': 'no_valid_guidance', 'frozen': False}
        if valid and 'hysynth-string' in arms:
            searched = runtime.search(case, out/'search', **({'images': images, 'resume': resume} if images or resume else {}))
            if searched.get('status') == 'program':
                guided = freeze(searched['expression'], grammar, expected, case, out/'hysynth', sha(out/'raw_pool.json'), 'hysynth_string_strict', images=images, resume=resume)
            else:
                guided = searched
        result = {'task_id': task['task_id'], 'origin': pool['origin'], 'model': pool['model'],
            'pool_sha256': sha(out/'raw_pool.json'), 'attempts': len(samples), 'valid_proposals': len(valid),
            'invalid_proposals': len(samples)-len(valid), 'training_consistent_proposals': sum(r.get('training_consistent', False) for r in rows),
            'unique_valid_expressions': len(set(expressions)), 'validation_counts': dict(Counter(r['status'] for r in rows)),
            'shared_pool': True, 'same_grammar': True, 'direct_dsl': direct, 'hysynth': guided,
            'guidance_sample_ids': [r['sample_id'] for r in valid],
            'new_model_requests': 0, 'heldout_or_behavioral_cases_used': False}
        hashes = {p.relative_to(out).as_posix(): sha(p) for p in out.rglob('*') if p.is_file() and p.name not in {'SHA256SUMS.json', 'result.json'}}
        hashes['result.json'] = digest(encoded(result))
        save(out/'SHA256SUMS.json', hashes)
        save(out/'result.json', result)
        return result
    except Exception as error:
        save(out/'adapter_error.json', {'type': type(error).__name__, 'message': str(error), 'prior_frozen_arms_preserved': True})
        raise

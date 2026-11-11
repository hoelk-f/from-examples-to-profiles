"""Program indexes and completion checks for a new synthesis run."""
from pathlib import Path
from .common import ROOT, ORDER, read, sha


def design(suite):
    return {(c, r, n) for c in ORDER
            for r in range(1, (1 if c in ORDER[:5] else 3 if suite == 'sensitivity' and c.startswith('hysynth') else 5) + 1)
            for n in ([2] if suite == 'main' else range(1, 6))}


def validate_index(programs):
    ids, slots = set(), set()
    for p in programs:
        slot = p['condition'], p['repeat'], p['examples'], p['task_id']
        if p['id'] in ids or slot in slots:
            raise ValueError('Duplicate program identity or synthesis slot.')
        if p['condition'] not in ORDER or p['system'] != p['condition'].partition('/')[0]:
            raise ValueError('Unknown or inconsistent program condition.')
        ids.add(p['id'])
        slots.add(slot)
    return programs


def collect(path, suite):
    path = Path(path)
    suite = 'sensitivity' if suite == 'sensitivity' else 'main'
    if path.is_file():
        programs=validate_index(read(path))
        if any((p['condition'],p['repeat'],p['examples']) not in design(suite) for p in programs):
            raise ValueError('Program index belongs to a different experiment design.')
        return programs, None
    tids = read(ROOT/'data/selection.json')['selected_tasks'] if suite == 'main' else read(ROOT/'data/sensitivity/protocol.json')['task_ids']
    expected = {(c, r, n, t) for c, r, n in design(suite) for t in tids}
    attempts, programs = {}, []
    for file in sorted(path.rglob('protocol.json')):
        protocol = read(file)
        if protocol.get('suite') != suite:
            continue
        folder = file.parent
        if not (folder/'outcomes.json').is_file() or not (folder/'programs.json').is_file():
            raise ValueError('Unfinished synthesis batch: ' + str(folder))
        outcomes = read(folder/'outcomes.json')
        if [x['task_id'] for x in outcomes] != protocol['task_ids']:
            raise ValueError('Unfinished synthesis batch: ' + str(folder))
        batch = validate_index(read(folder/'programs.json'))
        if {p['task_id'] for p in batch} != {x['task_id'] for x in outcomes if x['frozen']}:
            raise ValueError('Eligible programs disagree with synthesis outcomes.')
        prefix = protocol['condition'], protocol['repeat'], protocol['examples']
        if any((p['condition'], p['repeat'], p['examples']) != prefix for p in batch):
            raise ValueError('Programs disagree with their synthesis protocol.')
        for outcome in outcomes:
            slot = (*prefix, outcome['task_id'])
            if slot in attempts:
                raise ValueError('Duplicate synthesis attempt: ' + str(slot))
            attempts[slot] = outcome
        programs.extend(batch)
    if set(attempts) != expected:
        raise ValueError(f'Incomplete {suite} synthesis design: {len(expected-set(attempts))} missing, '
                         f'{len(set(attempts)-expected)} unexpected attempts. Finish synthesis before analysis.')
    programs.sort(key=lambda p: (ORDER.index(p['condition']), p['repeat'], p['examples'], p['task_id']))
    return validate_index(programs), dict(suite=suite, attempts=len(attempts), eligible=len(programs),
        outcomes=[dict(condition=c, repeat=r, examples=n, **value) for (c, r, n, t), value in sorted(attempts.items())])


def is_new(source, suite='main'):
    if source is None:
        return False
    manifest = Path(source)/(suite+'_execution.json')
    return manifest.is_file() and read(manifest).get('mode') == 'new'


def index(suite, source=None):
    if is_new(source, suite):
        return collect(Path(source)/(suite+'_programs.json'),suite)[0]
    return read(ROOT/'records'/(suite+'_programs.json'))


def check_source(source):
    if source is None:
        return
    source = Path(source)
    modes = set()
    for suite in ['main', 'random', 'selection', 'sensitivity']:
        manifest = read(source/(suite+'_execution.json'))
        receipt = read(source/(suite+'_validation.json'))
        if sha(source/(suite+'.jsonl.gz')) != receipt['observations_sha256']:
            raise ValueError('Changed execution observations: ' + suite)
        mode = manifest.get('mode', 'frozen')
        modes.add(mode)
        if mode == 'new':
            if sha(source/(suite+'_programs.json')) != receipt['program_index_sha256']:
                raise ValueError('Changed program index: ' + suite)
            programs = index(suite, source)
            if manifest.get('program_index', programs) != programs:
                raise ValueError('Program metadata disagrees with execution manifest: ' + suite)
            if [p['id'] for p in programs] != manifest['programs'] or {p['id']: p['sha256'] for p in programs} != manifest['program_hashes']:
                raise ValueError('Programs disagree with execution manifest: ' + suite)
    if len(modes) != 1 or modes - {'new', 'frozen'}:
        raise ValueError('Do not mix frozen and newly synthesized experiments.')
    if modes == {'new'}:
        main = {p['id']: p for p in index('main', source)}
        cohort = set(read(ROOT/'data/cohort.json')['task_ids'])
        expected = {pid: p for pid, p in main.items() if p['task_id'] in cohort}
        for suite in ['random', 'selection']:
            if {p['id']: p for p in index(suite, source)} != expected:
                raise ValueError('Execute the same new main programs on every test suite.')

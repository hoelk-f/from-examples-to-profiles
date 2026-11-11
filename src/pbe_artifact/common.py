from pathlib import Path
import csv
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
ORDER = ['synthphonia', 'merlin', 'prose', 'crossbeam', 'bustle',
         'direct-python/gpt-oss-120b', 'direct-python/qwen3.8-27b',
         'hysynth-string/gpt-oss-120b', 'hysynth-string/qwen3.8-27b']
OPS = ['V01', 'V02', 'V03', 'V04', 'V05', 'S01']


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    path = Path(path)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt') as stream:
        yield from (json.loads(line) for line in stream if line.strip())


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def table(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in data for key in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def csv_rows(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def task(tid):
    return read(ROOT / 'data/behavioral-unique-v2/tasks' / (tid + '.json'))


def cases(experiment, tid):
    if experiment == 'main':
        data = task(tid)
        result = [dict(case_id=x['base_id'], suite='training', input=x['input'], expected=x['expected_output'])
                  for x in data['behavioral']['bases']]
        result.extend(dict(case_id=f'{tid}-H{i}', suite='heldout', input=x['input'], expected=x['output'])
                      for i, x in enumerate(data['split']['heldout'], 1))
        result.extend(dict(case_id=x['case_id'], suite='behavioral', input=x['input'], expected=x['expected_output'])
                      for x in data['behavioral']['cases'])
        return result
    if experiment == 'random':
        return read(ROOT / 'data/random' / (tid + '.json'))['cases']
    if experiment == 'selection':
        return [dict(x, suite='new') for x in read(ROOT / 'data/selection/inputs' / (tid + '.json'))['execution_cases']]
    return read(ROOT / 'data/sensitivity/cases' / (tid + '.json'))


def passed(row, expected):
    return row['status'] == 'returned' and isinstance(row['actual'], str) and row['actual'] == expected


def observations(experiment, source=None):
    path = (Path(source) if source else ROOT / 'records') / (experiment + '.jsonl.gz')
    result = {}
    for row in rows(path):
        key = row['program_id'], row['suite'], row['case_id']
        if key in result:
            raise ValueError('Duplicate observation ' + str(key))
        if row['status'] not in {'returned', 'non_string_output', 'execution_error', 'execution_timeout', 'execution_process_error'}:
            raise ValueError('Incomplete observation ' + str(key))
        result[key] = row
    return result

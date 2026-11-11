"""Resolve saved artifacts at their current location without changing evidence."""
import os
from pathlib import Path


def suffix_after(value, marker):
    parts, marker = Path(value).parts, tuple(marker)
    starts = [i for i in range(len(parts) - len(marker) + 1)
              if parts[i:i + len(marker)] == marker]
    if len(starts) > 1:
        raise ValueError('Ambiguous saved artifact path: ' + str(value))
    return Path(*parts[starts[0] + len(marker):]) if starts else None


def contained(folder, relative):
    folder = Path(folder).resolve()
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Artifact path leaves its saved run.')
    path = (folder / relative).resolve()
    if path != folder and folder not in path.parents:
        raise ValueError('Artifact path leaves its saved run.')
    return path


def qualification_folder(output, value, system, tid):
    path = Path(value)
    if not path.is_absolute():
        return contained(output, path)
    for marker in [('programs', system, tid), ('dsl', tid)]:
        suffix = suffix_after(path, marker)
        if suffix is not None:
            return contained(output, Path(*marker) / suffix)
    raise ValueError('Unrecognized legacy qualification path: ' + str(value))


def program_path(root, record, index_path=None):
    value = Path(record['path'])
    base = record.get('path_base', 'repository')
    if base not in {'repository', 'index'}:
        raise ValueError('Unknown program path base: ' + str(base))
    if base == 'index':
        if index_path is None or value.is_absolute():
            raise ValueError('An index-relative program needs its programs.json location.')
        return (Path(index_path).resolve().parent / value).resolve()
    if index_path is not None:
        index = Path(index_path).resolve()
        info = record.get('study_run') or {}
        if all(k in info for k in ['system', 'model_slot', 'repeat']):
            job = ('jobs', info['system'], info['model_slot'], 'repeat-' + str(info['repeat']))
            suffix = suffix_after(value, (*job, 'synthesis'))
            parent = index.parent
            if suffix is not None and parent.name in {'synthesis', 'evaluation'} and tuple(parent.parent.parts[-4:]) == job:
                return contained(parent.parent / 'synthesis', suffix)
        # Old standalone synthesis runs used an absolute or repository-relative path.
        parent = index.parent
        if (parent / 'checkpoint.json').exists() or (parent / 'programs').is_dir() or (parent / 'dsl').is_dir():
            for marker in [('programs', record['system'], record['task_id']), ('programs', record['task_id']), ('dsl', record['task_id'])]:
                suffix = suffix_after(value, marker)
                if suffix is not None:
                    return contained(parent, Path(*marker) / suffix)
    return (Path(root) / value).resolve()


def index_record(record, path, index_path):
    return {**record, 'path': Path(os.path.relpath(Path(path).resolve(), Path(index_path).resolve().parent)).as_posix(),
            'path_base': 'index'}


def execution_record(root, record, index_path):
    result = {**record, 'path': str(program_path(root, record, index_path))}
    result.pop('path_base', None)
    return result


def request_key(folder, journal):
    path, base = Path(folder), Path(journal).resolve().parent
    if not path.is_absolute():
        return contained(base, path).relative_to(base).as_posix()
    try:
        return path.resolve().relative_to(base).as_posix()
    except ValueError:
        for marker in [('requests', 'direct-python'), ('dsl',)]:
            suffix = suffix_after(path, marker)
            if suffix is not None:
                return contained(base, Path(*marker) / suffix).relative_to(base).as_posix()
    raise ValueError('Unrecognized legacy request path: ' + str(folder))

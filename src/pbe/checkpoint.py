"""Small, durable checkpoints for explicitly resumable runs."""
from contextlib import contextmanager
from pathlib import Path
import fcntl
import json
import os
import uuid
from .io import read, write, new_run


def retain(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise ValueError('Checkpoint identity changed: ' + str(path))
    else:
        write(path, value)


def folder(root, kind, output, resume):
    if not resume:
        return new_run(root, kind, output)
    if output is None:
        raise ValueError('--resume requires an existing --output directory.')
    target = Path(output).resolve()
    protected = [root / p for p in ['data', 'artifacts', 'results/published', 'experiments', 'src', 'runtimes']]
    if any(target == p.resolve() or p.resolve() in target.parents for p in protected):
        raise ValueError('Cannot resume inside reference artifacts.')
    if not target.is_dir():
        raise ValueError('Resume directory does not exist: ' + str(target))
    return target


@contextmanager
def lock(folder):
    with (Path(folder) / '.run.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Another process is using this run: ' + str(folder)) from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def journal(path):
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        cut = raw.rfind(b'\n') + 1
        # Keep the torn tail as evidence before resuming the unfinished observation.
        saved = path.with_name(path.name + '.torn-' + uuid.uuid4().hex)
        saved.write_bytes(raw[cut:])
        with path.open('r+b') as stream:
            stream.truncate(cut)
            stream.flush()
            os.fsync(stream.fileno())
        raw = raw[:cut]
    return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line]


def append(stream, row):
    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    stream.flush()
    os.fsync(stream.fileno())

from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
import uuid


def repository():
    root = Path(os.environ.get("PBE_ROOT", Path(__file__).resolve().parents[2])).resolve()
    if not (root / "experiments/main.json").is_file():
        raise ValueError("Run from an editable repository installation or set PBE_ROOT.")
    return root


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def records(path):
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def new_run(root, kind, output=None):
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + kind + "-" + uuid.uuid4().hex[:8]
    folder = Path(output).resolve() if output else root / "runs" / name
    protected = [root / p for p in ["data", "artifacts", "results/published", "experiments", "src", "runtimes"]]
    if any(folder == p or p in folder.parents for p in protected):
        raise ValueError("Choose an output directory outside the reference artifacts.")
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def selection(root, experiment="main", system=None, task=None):
    if not experiment.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Invalid experiment name.")
    config_path = root / "experiments" / (experiment + ".json")
    check_reference(root, config_path)
    cfg = read(config_path)
    systems = system.split(",") if system else cfg["systems"]
    tasks = task.split(",") if task else cfg["task_ids"]
    if not systems or len(set(systems)) != len(systems) or set(systems) - set(cfg["systems"]):
        raise ValueError("Unknown or repeated system. Choices: " + ", ".join(cfg["systems"]))
    if not tasks or len(set(tasks)) != len(tasks) or set(tasks) - set(cfg["task_ids"]):
        raise ValueError("Task is not part of this experiment, or is repeated.")
    return {**cfg, "systems": systems, "task_ids": tasks}


def task_path(root, cfg, tid):
    snapshot = cfg.get('task_set')
    if snapshot:
        if cfg.get('evaluation_task_set'):
            raise ValueError('Choose one versioned task set.')
        if tid not in snapshot['hashes']:
            raise ValueError('Task is outside the versioned task set: ' + tid)
        path = (root / snapshot['directory'] / (tid + '.json')).resolve()
        if not path.is_relative_to((root / 'data').resolve()):
            raise ValueError('Versioned task sets must be stored under data/.')
        if sha(path) != snapshot['hashes'][tid]:
            raise ValueError('Task snapshot changed: ' + tid)
        return path
    snapshot = cfg.get('evaluation_task_set')
    if snapshot:
        if not cfg.get('evaluation_only') or tid not in snapshot['hashes']:
            raise ValueError('A versioned evaluation task set is required.')
        path = root / snapshot['directory'] / (tid + '.json')
        if sha(path) != snapshot['hashes'][tid]:
            raise ValueError('Evaluation task snapshot changed: ' + tid)
        return path
    return root / 'data/tasks' / (tid + '.json')


def tasks_for(root, cfg):
    result = {}
    for tid in cfg["task_ids"]:
        path = task_path(root, cfg, tid)
        check_reference(root, path)
        result[tid] = read(path)
    return result


def cases(task):
    tid = task["task_id"]
    result = {("heldout", f"{tid}-H{i+1}"): {"input": x["input"], "expected": x["output"]}
              for i, x in enumerate(task["split"]["heldout"])}
    for x in task["behavioral"].get("cases", []):
        result[("behavioral", x["case_id"])] = {"input": x["input"], "expected": x["expected_output"]}
    return result


def verified_program(root, record, index_path=None):
    from .paths import program_path
    path = program_path(root, record, index_path)
    if sha(path) != record["sha256"]:
        raise ValueError("Program checksum mismatch: " + record["path"])
    if record.get("grammar") and sha(root / record["grammar"]) != record["grammar_sha256"]:
        raise ValueError("Grammar checksum mismatch: " + record["grammar"])
    return read(path) if path.suffix == ".json" else path.read_text(encoding="utf-8")


def check_reference(root, path):
    path = Path(path).resolve()
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        return
    manifest = root / "checksums.json"
    if manifest.exists():
        expected = read(manifest).get(relative)
        if expected and sha(path) != expected:
            raise ValueError("Frozen reference changed: " + relative)

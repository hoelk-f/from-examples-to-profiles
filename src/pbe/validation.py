from collections import defaultdict
from pathlib import PurePosixPath
import re
from .io import read, sha, verified_program
from .contract import extract
from .behavioral import generate


def normalized(value):
    if isinstance(value, dict):
        return {k: normalized(v) for k,v in value.items() if k != "execution_status"}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    return value


def verify_provenance(root, tasks):
    def local_file(reference):
        name, _, fragment = reference.partition("#")
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("Broken provenance path: " + reference)
        if fragment:
            value = read(path)
            for key in fragment.split("."):
                if not isinstance(value, dict) or key not in value:
                    raise ValueError("Broken provenance fragment: " + reference)
                value = value[key]
        return path

    sources = read(root / "data/sources.json")
    files = read(local_file(sources["files"]))
    occurrences = read(local_file(sources["occurrences"]))["occurrences"]
    plan = read(local_file(sources["behavioral_plan"]))
    experiment = read(local_file(sources["experiment"]))
    for field in ["cohort", "program_manifest", "source_manifest", "task_contract"]:
        local_file(plan[field])
    local_file(plan["primary_analysis"]["task_selection"])
    local_file(plan["secondary_analysis"]["computed_by"])
    local_file(plan["evaluation_protocol"]["limits"])
    if plan["cohort"] != sources["experiment"] or plan["program_manifest"] != experiment["programs"]:
        raise ValueError("Behavioral plan and experiment references differ.")
    for reference, record in files.items():
        path = PurePosixPath(record["path"])
        if path.is_absolute() or ".." in path.parts or "\\" in record["path"]:
            raise ValueError("Source path must be relative to its upstream repository: " + reference)
        if not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
            raise ValueError("Invalid source checksum: " + reference)
        if "zip_member" in record:
            expected_url = f'{record["repository"]}/releases/download/{record["release"]}/{record["path"]}'
            expected_reference = expected_url + "!" + record["zip_member"]
            if not re.fullmatch(r"[0-9a-f]{64}", record["container_sha256"]):
                raise ValueError("Invalid archive checksum: " + reference)
        else:
            if not re.fullmatch(r"[0-9a-f]{40}", record["commit"]):
                raise ValueError("Source file needs a pinned commit: " + reference)
            expected_url = f'{record["repository"]}/blob/{record["commit"]}/{record["path"]}'
            expected_reference = expected_url
        if record["url"] != expected_url or reference != expected_reference:
            raise ValueError("Source reference does not match its upstream location: " + reference)

    def check_refs(value):
        if isinstance(value, dict):
            for key, item in value.items():
                refs = item if key == "source_files" else [item] if key == "file_ref" else []
                for reference in refs:
                    if reference not in files:
                        raise ValueError("Unknown source-file reference: " + reference)
                check_refs(item)
        elif isinstance(value, list):
            for item in value:
                check_refs(item)

    occurrence_ids = {row["occurrence_id"] for row in occurrences}
    if len(occurrence_ids) != len(occurrences):
        raise ValueError("Duplicate source occurrence.")
    check_refs(occurrences)
    for task in tasks:
        if set(task["occurrences"]) - occurrence_ids:
            raise ValueError("Unknown source occurrence in " + task["task_id"])
        check_refs(task)
        for base in task["behavioral"].get("bases", []):
            expected = f'data/tasks/{task["task_id"]}.json#split.training'
            if base["source_path"] != expected:
                raise ValueError("Incorrect behavioral base provenance: " + task["task_id"])
    return {"source_files": len(files), "source_occurrences": len(occurrences)}


def verify(root):
    manifest = read(root / "checksums.json")
    for name, expected in manifest.items():
        path = root / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError("Reference artifact changed: " + name)
    tasks = [read(p) for p in sorted((root / "data/tasks").glob("T*.json"))]
    if {t["task_id"] for t in tasks} != {f"T{i:03}" for i in range(1, len(tasks) + 1)}:
        raise ValueError("Task IDs must form one contiguous three-digit sequence.")
    seeds = [t.get("generation_seed") for t in tasks]
    if any(type(seed) is not int or seed < 1 for seed in seeds) or len(set(seeds)) != len(tasks):
        raise ValueError("Each task needs a unique positive generation seed.")
    provenance = verify_provenance(root, tasks)
    source_count = 0
    for task in tasks:
        original = {(e["input"][0], e["output"]) for e in task["examples"]}
        training = [(e["input"], e["output"]) for e in task["split"]["training"]]
        heldout = [(e["input"], e["output"]) for e in task["split"]["heldout"]]
        if len(training) != 2 or set(training) & set(heldout) or set(training + heldout) != original or len(training + heldout) != len(original):
            raise ValueError("Invalid source split: " + task["task_id"])
        for value, expected in original:
            if extract(value, task["parameters"]["selector"])[0] != expected:
                raise ValueError("Source example violates recorded contract: " + task["task_id"])
        source_count += len(original)
    programs = read(root / "artifacts/programs/index.json")
    for record in programs.values():
        verified_program(root, record)
    dsl_programs = read(root / 'artifacts/programs/dsl-pilot/index.json')
    for record in dsl_programs.values():
        verified_program(root, record)
    main = read(root / "experiments/main.json")
    if main["task_ids"] != [f"T{i:03}" for i in range(1, len(main["task_ids"]) + 1)]:
        raise ValueError("The main cohort must occupy the first task IDs.")
    selected = {t["task_id"]:t for t in tasks if t["task_id"] in main["task_ids"]}
    generated = generate([selected[tid] for tid in main["task_ids"]])
    bytask = defaultdict(lambda: defaultdict(list))
    for category, rows in generated.items():
        for row in rows:
            bytask[row["task_id"]][category].append(row)
    for tid, task in selected.items():
        if normalized(dict(bytask[tid])) != normalized(task["behavioral"]):
            raise ValueError("Behavioral generation differs from the frozen suite: " + tid)
    return {"verified_files": len(manifest), **provenance, "tasks": len(tasks), "source_pairs": source_count, "programs": len(programs), "regenerated_behavioral_cases": len(generated["cases"]), "regenerated_obligations": len(generated["obligations"]), "passed": True}

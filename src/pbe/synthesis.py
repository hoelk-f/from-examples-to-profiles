from collections import Counter
from .io import read, write, sha, new_run, tasks_for
from .runtime import ensure, CLASSIC
from .paths import index_record


def path_ref(root, path):
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def messages(request):
    value = request.get("messages") or request.get("body", {}).get("messages") or request.get("payload", {}).get("messages")
    if not isinstance(value, list):
        raise ValueError("Prepared request has no messages.")
    return value


def synthesize(root, cfg, output=None, live=False, provider_file=None, pool_dir=None, resume=False, retry_uncertain=False):
    if cfg.get('evaluation_only'):
        raise ValueError('This experiment only evaluates frozen programs. Synthesis is disabled.')
    from .systems import dsl
    if cfg.get('runtime_images') and not cfg.get('runtime_rebuild', {}).get('synthesis_allowed'):
        raise ValueError('This runtime version is for frozen-program evaluation only.')
    if cfg.get('resume_protocol') == 1:
        from .resumable import synthesize as resumable_synthesis
        return resumable_synthesis(root, cfg, output, live, provider_file, pool_dir, resume, retry_uncertain)
    if resume or retry_uncertain:
        raise ValueError('Resume requires an experiment with resume_protocol 1.')
    from .study import validate_identity, timestamp
    from uuid import uuid4
    provider_config = read(provider_file) if provider_file else None
    validate_identity(cfg, provider_config, live)
    cfg = {**cfg, 'run_id': uuid4().hex, 'started_at': timestamp()}
    systems = cfg["systems"]
    if set(systems) - (set(CLASSIC) | {"direct-python"} | dsl.SYSTEMS):
        raise ValueError("Unsupported synthesis method.")
    if live and not provider_file:
        raise ValueError("--live requires --provider CONFIG.json.")
    if provider_file and not live:
        raise ValueError("Use --live explicitly when supplying a provider.")
    dsl_systems = [s for s in systems if s in dsl.SYSTEMS]
    if pool_dir and (live or not dsl_systems):
        raise ValueError('--pool-dir is only for recorded DSL synthesis.')
    task_data = tasks_for(root, cfg)
    preparations = {}
    if dsl_systems:
        for tid, task in task_data.items():
            examples = [{'input': e['input'], 'output': e['output']} for e in task['split']['training']]
            preparations[tid] = dsl.prepared(root, cfg, tid, examples, pool_dir, live)
    provider = None
    if live:
        from .provider import Provider
        if "direct-python" not in systems and not dsl_systems:
            raise ValueError("Selected systems do not use an LLM.")
        count = len(cfg['task_ids']) if 'direct-python' in systems else 0
        count += sum(p['plan']['attempts_per_task'] for p in preparations.values())
        provider = Provider(provider_config, count)
        cfg = {**cfg, "model": provider.config["model"]}
    ensure(root, systems, synthesis=True)
    out = new_run(root, "synthesize", output)
    write(out / "selection.json", cfg)
    if provider:
        write(out / "provider.json", provider.config)
    index, outcomes = {}, []
    write(out / 'programs.json', index)
    write(out / 'outcomes.json', outcomes)
    active = []
    tid = None
    try:
        for tid, task in task_data.items():
            examples = [{"input": e["input"], "output": e["output"]} for e in task["split"]["training"]]
            active = dsl_systems
            dsl_results = dsl.run(preparations[tid], dsl_systems, out/'dsl'/tid, out/'pools'/f'{tid}.json', provider) if dsl_systems else {}
            for system in systems:
                active = [system]
                folder = out / "programs" / system / tid
                if system in CLASSIC:
                    from .systems.synthesis import run_one
                    result = run_one(CLASSIC[system], {"task_id": tid, "examples": examples}, folder)
                elif system in dsl.SYSTEMS:
                    result, folder = dsl_results[system]
                else:
                    from .systems.direct import direct
                    folder.mkdir(parents=True)
                    original = root / "artifacts/llm/legacy/direct" / tid
                    answer = provider.complete(messages(read(original / "request.json")), out / "requests" / system / tid)["text"] if live else (original / "response.txt").read_text(encoding="utf-8")
                    (folder / "response.txt").write_text(answer, encoding="utf-8")
                    result = direct(read(root / "runtimes/legacy/configuration.json"), folder, answer, examples)
                    write(folder / "result.json", result)
                if result.get("frozen"):
                    path = folder / result["program_file"]
                    index[system + "/" + tid] = index_record({"system": system, "task_id": tid, "sha256": sha(path), "runtime": system, "run_id": cfg["run_id"], "study_run": cfg.get("study_run")}, path, out / 'programs.json')
                    if system in dsl.SYSTEMS:
                        grammar = preparations[tid]['taskdir']/'task.native.sl'
                        index[system+'/'+tid].update(runtime='hysynth-string', grammar=path_ref(root,grammar),
                            grammar_sha256=sha(grammar),pool_sha256=result['pool_sha256'])
                    write(out / "programs.json", index)
                outcomes.append({"system": system, "task_id": tid, "status": result["status"], "frozen": result.get("frozen", False), "run_id": cfg["run_id"], "study_run": cfg.get("study_run")})
                write(out / "outcomes.json", outcomes)
                print(system, tid, result["status"], flush=True)
                if result["status"] in ["initialization_error", "initialization_timeout", "protocol_error", "adapter_error"]:
                    raise RuntimeError("Synthesis stopped on an infrastructure failure.")
        write(out / "status.json", {"status": "completed", "jobs": len(outcomes), "frozen": len(index), "counts": dict(Counter(x["system"] + ":" + x["status"] for x in outcomes)), "new_model_requests": provider.completed if provider else 0, "llm_source": "live" if live else "recorded", "heldout_or_behavioral_answers_used": False, "finished_at": timestamp()})
    except BaseException as error:
        recorded = {(r['system'], r['task_id']) for r in outcomes}
        for system in active:
            if (system, tid) not in recorded:
                outcomes.append({'system': system, 'task_id': tid, 'status': 'interrupted',
                    'frozen': system + '/' + tid in index, 'error_type': type(error).__name__,
                    'run_id': cfg['run_id'], 'study_run': cfg.get('study_run')})
        write(out / 'outcomes.json', outcomes)
        write(out / "status.json", {"status": "interrupted", "error": str(error), "completed_jobs": len(outcomes), "new_model_requests": provider.completed if provider else 0})
        raise
    print(out)
    return out

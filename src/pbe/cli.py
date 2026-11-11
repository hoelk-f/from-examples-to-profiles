import argparse
from pathlib import Path
import json
import sys
from .io import repository, selection, read, write, sha


def parser():
    p = argparse.ArgumentParser(prog="pbe", description="Reproduce PBE results, run frozen programs, or synthesize new ones.")
    sub = p.add_subparsers(dest="command", required=True)
    for name, helptext in [("report", "Recompute metrics from saved predictions"), ("evaluate", "Run frozen programs using Docker"), ("synthesize", "Create new programs using fixed synthesis examples")]:
        c = sub.add_parser(name, help=helptext)
        c.add_argument("--experiment", default="main", help="Experiment configuration name")
        c.add_argument("--system", help="System name, optionally comma-separated")
        c.add_argument("--task", help="Task ID, optionally comma-separated")
        c.add_argument("--output", type=Path, help="New output directory, defaults to runs/")
        if name != "report":
            c.add_argument("--resume", action="store_true", help="Continue an existing output without replacing completed work")
        if name == "report":
            c.add_argument("--from", dest="source", type=Path, help="Result directory, defaults to published results")
        elif name == "evaluate":
            c.add_argument("--programs", type=Path, help="Program index from a new synthesis run")
        else:
            c.add_argument("--retry-uncertain", action="store_true", help="Explicitly allow bounded retries after uncertain transport failures")
            c.add_argument("--live", action="store_true", help="Make new LLM requests using an explicit provider configuration")
            c.add_argument("--provider", type=Path, help="JSON provider configuration. API key stays in its environment variable")
            c.add_argument("--pool-dir", type=Path, help="Reuse recorded DSL pools from a previous synthesis run")
    c = sub.add_parser("study", help="Prepare, explicitly run, or summarize repeated LLM conditions")
    c.add_argument("action", choices=["plan", "run", "report", "cohort"])
    c.add_argument("--experiment", default="llm-stability")
    c.add_argument("--bindings", type=Path, help="JSON object mapping model slots to provider configurations")
    c.add_argument("--from", dest="source", type=Path, help="Prepared study directory or study.json")
    c.add_argument("--output", type=Path, help="New plan or report directory")
    c.add_argument("--live", action="store_true", help="Explicitly enable new model requests for study run")
    c.add_argument("--resume", action="store_true", help="Resume incomplete jobs with their saved responses")
    c.add_argument("--retry-uncertain", action="store_true", help="Explicitly allow bounded retries after uncertain transport failures")
    c.add_argument("--condition", help="Run one condition, for example direct-python/model-a")
    c.add_argument("--repeat", type=int, help="Run one planned repetition")
    c.add_argument("--include-classical", action="store_true", help="Report the five fixed classical systems with the study on common task sets")
    c = sub.add_parser('extension', help='Plan, run, or report additional tests on existing frozen programs')
    c.add_argument('action', choices=['plan', 'run', 'report'])
    c.add_argument('--experiment', default='behavioral-extension-v1')
    c.add_argument('--from', dest='source', required=True, type=Path, help='Original study for plan, extension directory for run or report')
    c.add_argument('--output', type=Path, help='New plan or report directory')
    c.add_argument('--resume', action='store_true')
    c.add_argument('--workers', type=int, default=1, help='Concurrent evaluation jobs, at most four')
    c.add_argument('--condition', help='Evaluate one condition')
    c.add_argument('--repeat', type=int, help='Evaluate one original repetition')
    c = sub.add_parser("inspect", help="Read one task and its frozen programs")
    c.add_argument("task")
    c.add_argument("--json", action="store_true", help="Print the complete task record")
    c = sub.add_parser("verify", help="Check artifact hashes, splits, and task contracts")
    c = sub.add_parser("runtime", help="Check or transfer pinned Docker runtimes")
    c.add_argument("action", choices=["check", "export", "load"])
    c.add_argument("path", nargs="?", type=Path)
    c.add_argument("--system", help="Check one system")
    c.add_argument("--experiment", default="main", help="Runtime selection from a versioned experiment")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        root = repository()
        if args.command in ["report", "evaluate", "synthesize"]:
            if args.command == "synthesize" and not args.system:
                raise ValueError("Choose a system with --system.")
            saved_path = None
            if args.command == 'report' and args.source:
                saved_path = args.source/'selection.json'
            elif args.command == 'evaluate' and args.programs:
                saved_path = args.programs.parent/'selection.json'
            if saved_path and saved_path.is_file():
                saved = read(saved_path)
                cfg = selection(root, saved['id'], args.system or ','.join(saved['systems']), args.task or ','.join(saved['task_ids']))
                if cfg.get('version') != saved.get('version'):
                    raise ValueError('Saved run uses a different experiment version.')
                if saved.get('study_run') and (cfg['systems'] != saved['systems'] or not set(cfg['task_ids']) <= set(saved['task_ids'])):
                    raise ValueError('A study report cannot change its method or add tasks to a saved job.')
                for key in ['study_run', 'run_id', 'started_at', 'model', 'evaluation_task_set', 'extension_run']:
                    if key in saved:
                        cfg[key] = saved[key]
            else:
                cfg = selection(root, args.experiment, args.system, args.task)
            if args.command == "report":
                from .analysis import report
                report(root, cfg, args.source, args.output)
            elif args.command == "evaluate":
                from .evaluation import evaluate
                evaluate(root, cfg, args.output, args.programs, resume=args.resume)
            else:
                from .synthesis import synthesize
                synthesize(root, cfg, args.output, args.live, args.provider, args.pool_dir, resume=args.resume, retry_uncertain=args.retry_uncertain)
        elif args.command == "study":
            from .study import plan, run
            if args.action == 'plan':
                if args.source or args.live or args.condition or args.repeat or args.resume or args.retry_uncertain or args.include_classical:
                    raise ValueError('study plan accepts --experiment, --bindings and --output.')
                plan(root, selection(root, args.experiment), args.output, args.bindings)
            else:
                if not args.source or args.bindings:
                    raise ValueError('Use --from with a prepared study. Bind models when preparing a plan.')
                if args.action == 'run':
                    if args.include_classical:
                        raise ValueError('--include-classical is for offline study report only.')
                    if args.output:
                        raise ValueError('Study jobs write to their planned directories.')
                    run(root, args.source, args.live, args.condition, args.repeat, args.resume, args.retry_uncertain)
                elif args.action == 'cohort':
                    if args.live or args.condition or args.repeat or args.resume or args.retry_uncertain or args.include_classical:
                        raise ValueError('study cohort accepts --from and --output.')
                    from .replacement import report_cohort
                    report_cohort(root, args.source, args.output)
                else:
                    if args.live or args.condition or args.repeat or args.resume or args.retry_uncertain:
                        raise ValueError('study report always includes all planned jobs and makes no model requests.')
                    if args.include_classical:
                        from .comparison import report_combined
                        report_combined(root, args.source, args.output)
                    else:
                        from .study_analysis import report_study
                        report_study(root, args.source, args.output)
        elif args.command == 'extension':
            from .extension import plan as extension_plan, run as extension_run, report as extension_report
            if args.action == 'plan':
                if args.resume or args.workers != 1 or args.condition or args.repeat:
                    raise ValueError('extension plan accepts --experiment, --from and --output.')
                extension_plan(root, selection(root, args.experiment), args.source, args.output)
            elif args.action == 'run':
                if args.output:
                    raise ValueError('Extension jobs write to their planned directories.')
                extension_run(root, args.source, args.resume, args.workers, args.condition, args.repeat)
            else:
                if args.resume or args.workers != 1 or args.condition or args.repeat:
                    raise ValueError('extension report accepts --from and --output.')
                extension_report(root, args.source, args.output)
        elif args.command == "inspect":
            if len(args.task) != 4 or not args.task.startswith("T") or not args.task[1:].isdigit():
                raise ValueError("Use a task ID such as T031.")
            task = read(root / "data/tasks" / (args.task + ".json"))
            if args.json:
                print(json.dumps(task, ensure_ascii=False, indent=2))
            else:
                print(task["task_id"], task["field"])
                print("Sources:", ", ".join(task["collections"]))
                print("Selector:", json.dumps(task["parameters"]["selector"], ensure_ascii=False))
                print("Synthesis examples:")
                for row in task["split"]["training"]:
                    print(" ", repr(row["input"]), "->", repr(row["output"]))
                print("Held-out:", len(task["split"]["heldout"]), "Behavioral:", len(task["behavioral"].get("cases", [])))
                print("Programs:")
                programs = read(root / "artifacts/programs/index.json")
                programs.update(read(root / 'artifacts/programs/dsl-pilot/index.json'))
                for key, rec in programs.items():
                    if rec["task_id"] == args.task:
                        print(" ", rec["system"], rec["path"])
        elif args.command == "verify":
            from .validation import verify
            print(json.dumps(verify(root), indent=2))
        elif args.command == "runtime":
            from .runtime import ensure, export_bundle, load_bundle
            if args.action == "check":
                cfg = selection(root, args.experiment)
                systems = args.system.split(',') if args.system else cfg['systems']
                print(json.dumps(ensure(root, systems, synthesis=True, overrides=cfg.get('runtime_images')), indent=2))
            elif args.path is None:
                raise ValueError("Provide a bundle directory.")
            elif args.action == "export":
                cfg = selection(root, args.experiment)
                systems = args.system.split(',') if args.system else cfg['systems']
                export_bundle(root, args.path, systems, overrides=cfg.get('runtime_images'))
            else:
                load_bundle(root, args.path)
        return 0
    except KeyboardInterrupt:
        print("Interrupted. Partial results are preserved.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"pbe: {error}", file=sys.stderr)
        return 1

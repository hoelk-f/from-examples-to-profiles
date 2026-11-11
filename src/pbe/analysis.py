from collections import defaultdict, Counter
from fractions import Fraction
import csv
from .io import records, cases, tasks_for, read, write, new_run, check_reference, verified_program
from .scoring import score, assertion_key, cells
from .reporting import profile_matrix, summary_rows, render_report


def metric(values):
    total = sum(len(v) for v in values.values())
    correct = sum(sum(v) for v in values.values())
    return {"tasks": len(values), "cases": total, "correct": correct,
            "macro": float(sum((Fraction(sum(v), len(v)) for v in values.values()), Fraction()) / len(values)) if values else None,
            "micro": correct / total if total else None,
            "fully_passing_tasks": sum(all(v) for v in values.values())}


def csv_write(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(root, cfg, predictions, bases):
    tasks = tasks_for(root, cfg)
    expected = {tid: cases(task) for tid, task in tasks.items()}
    selected = set(cfg["systems"])
    index = {}
    outcomes = defaultdict(Counter)
    for row in predictions:
        system, tid = row["system"], row["task_id"]
        if system not in selected or tid not in tasks:
            continue
        key = system, tid, row["suite"], row["case_id"]
        if key in index:
            raise ValueError("Duplicate prediction: " + str(key))
        case = expected[tid].get((row["suite"], row["case_id"]))
        if case is None or row["input"] != case["input"] or row["expected"] != case["expected"]:
            raise ValueError("Prediction does not match the fixed case: " + str(key))
        if row["status"] not in {"returned", "execution_error", "non_string_output", "execution_timeout", "execution_process_error"}:
            raise ValueError("Infrastructure or unknown status cannot be scored: " + row["status"])
        passed = row["status"] == "returned" and isinstance(row["actual"], str) and row["actual"] == case["expected"]
        if "passed" in row and row["passed"] != passed:
            raise ValueError("Stored verdict differs from recomputed exact match: " + str(key))
        index[key] = {**row, "passed": passed}
        outcomes[system][row["status"]] += 1
    required = {(s, tid, suite, cid) for s in selected for tid in tasks for suite, cid in expected[tid]}
    if set(index) != required:
        raise ValueError(f"Incomplete evaluation: {len(required - set(index))} predictions missing.")
    base_index = {}
    expected_bases = {(tid, b["base_id"]): b for tid, task in tasks.items() for b in task["behavioral"].get("bases", [])}
    for row in bases:
        if row["system"] not in selected or row["task_id"] not in tasks:
            continue
        key = row["system"], row["base_id"]
        target = expected_bases.get((row["task_id"], row["base_id"]))
        if key in base_index or target is None or row["input"] != target["input"] or row["expected"] != target["expected_output"]:
            raise ValueError("Invalid or duplicate base observation: " + str(key))
        base_index[key] = row
    summary, task_rows, operator_rows, profile_rows = [], [], [], []
    full = {}
    operator_cases = defaultdict(lambda: defaultdict(set))
    for tid, task in tasks.items():
        for ob in task["behavioral"].get("obligations", []):
            if ob.get("status") == "planned":
                operator_cases[ob["operator_id"]][tid].add(ob["case_id"])
    for system in cfg["systems"]:
        suite_metrics = {}
        full[system] = {}
        for suite in ["heldout", "behavioral"]:
            values = {tid: [index[system, tid, su, cid]["passed"] for su, cid in expected[tid] if su == suite] for tid in tasks}
            values = {tid: v for tid, v in values.items() if v}
            suite_metrics[suite] = metric(values)
            full[system][suite] = {tid for tid, v in values.items() if all(v)}
            for tid, vals in values.items():
                task_rows.append({"system": system, "task_id": tid, "suite": suite, "cases": len(vals), "correct": sum(vals), "accuracy": sum(vals)/len(vals), "fully_passed": all(vals)})
        summary.append({"system": system, **suite_metrics, "new_behavioral_failures_after_heldout_pass": len(full[system]["heldout"] - full[system]["behavioral"]), "outcomes": dict(outcomes[system])})
        for op, bytask in operator_cases.items():
            vals = {tid: [index[system, tid, "behavioral", cid]["passed"] for cid in cids] for tid, cids in bytask.items()}
            baseline = {tid: [index[system, tid, su, cid]["passed"] for su, cid in expected[tid] if su == "heldout"] for tid in bytask}
            operator_rows.append({"system": system, "operator": op, "expectation": "Exact Output", **metric(vals), "matched_heldout_macro": metric(baseline)["macro"]})
        buckets = defaultdict(lambda: defaultdict(dict))
        relation_operators = defaultdict(lambda: defaultdict(dict))
        parameters = defaultdict(lambda: defaultdict(dict))
        for tid, task in tasks.items():
            for ob in task["behavioral"].get("obligations", []):
                if ob.get("status") != "planned":
                    continue
                variant = index[system, tid, "behavioral", ob["case_id"]]
                for assertion in ob["assertions"]:
                    base = base_index.get((system, assertion.get("base_id")))
                    if assertion["expectation"] != "Exact Output" and base is None:
                        raise ValueError("Missing observed base output for " + str((system, tid, assertion.get("base_id"))))
                    passed = score(assertion, variant, base)
                    key = assertion_key(ob, assertion)
                    if assertion["expectation"] != "Exact Output":
                        relation_operators[(ob["operator_id"], assertion["expectation"])][tid][key] = passed
                    for parameter in ["factor", "side"]:
                        if parameter in ob["parameter"]:
                            parameters[(ob["operator_id"], parameter + "=" + str(ob["parameter"][parameter]), assertion["expectation"])][tid][key] = passed
                    for cell in cells(ob, assertion):
                        buckets[cell][tid][key] = passed
        for (op, expectation), bytask in sorted(relation_operators.items()):
            baseline = {tid: [index[system, tid, su, cid]["passed"] for su, cid in expected[tid] if su == "heldout"] for tid in bytask}
            operator_rows.append({"system": system, "operator": op, "expectation": expectation, **metric({t: list(v.values()) for t,v in bytask.items()}), "matched_heldout_macro": metric(baseline)["macro"]})
        for cell, bytask in sorted(buckets.items()):
            profile_rows.append({"system": system, "profile_kind": "taxonomy", "operator": "", "parameter": "", "dimension": cell[0], "regime_family": cell[1], "regime": cell[2], "expectation": cell[3], **metric({t: list(v.values()) for t,v in bytask.items()})})
        for (op, parameter, expectation), bytask in sorted(parameters.items()):
            profile_rows.append({"system": system, "profile_kind": "parameter", "operator": op, "parameter": parameter, "dimension": "", "regime_family": "", "regime": "", "expectation": expectation, **metric({t: list(v.values()) for t,v in bytask.items()})})
    common = set.intersection(*(full[s]["heldout"] for s in cfg["systems"]))
    result = {"schema_version": 1, "experiment": cfg["id"], "task_count": len(tasks), "systems": summary,
              "common_heldout_pass": {"tasks": sorted(common, key=lambda t: int(t[1:])), "new_failures": {s: len(common - full[s]["behavioral"]) for s in cfg["systems"]}}}
    return result, task_rows, operator_rows, profile_rows


def report(root, cfg, source=None, output=None):
    if cfg.get("kind") == "synthesis":
        return coverage_report(root, cfg, output)
    folder = Path(source) if source else root / "results/published" / cfg["id"]
    prediction_file = next((folder / n for n in ["predictions.jsonl.gz", "predictions.jsonl"] if (folder / n).exists()), None)
    base_file = next((folder / n for n in ["bases.jsonl.gz", "bases.jsonl"] if (folder / n).exists()), None)
    evidence_files = [p for p in [prediction_file, base_file] if p is not None]
    if not evidence_files and not (folder / 'programs.json').exists() and not (folder / 'outcomes.json').exists():
        raise ValueError("No saved evaluation or synthesis results found. Use --from with a run directory.")
    for path in evidence_files:
        check_reference(root, path)
    predictions = list(records(prediction_file)) if prediction_file else []
    bases = list(records(base_file)) if base_file else []
    program_path = folder / 'programs.json'
    if not program_path.exists() and cfg.get('programs'):
        program_path = root / cfg['programs']
    check_reference(root, program_path)
    programs = read(program_path) if program_path.exists() else {}
    for rec in programs.values():
        if rec['system'] in cfg['systems'] and rec['task_id'] in cfg['task_ids']:
            verified_program(root, rec, program_path)
    outcomes = read(folder / 'outcomes.json') if (folder / 'outcomes.json').exists() else []
    from .assessment import assess, export, coverage_text
    assessment = assess(root, cfg, predictions, bases, programs, outcomes)
    if assessment['complete']:
        result, task_rows, operators, profiles = summarize(root, cfg, predictions, bases)
    else:
        result = {k: assessment[k] for k in ['schema_version', 'experiment', 'task_count', 'systems', 'complete']}
        task_rows, operators, profiles = assessment['task_rows'], [], assessment['profiles']
    out = new_run(root, "report", output)
    write(out / "selection.json", cfg)
    write(out / "summary.json", result)
    csv_write(out / "tasks.csv", task_rows)
    csv_write(out / "operators.csv", operators)
    csv_write(out / "profiles.csv", profiles)
    write(out / "profiles.json", {"operators": operators, "profiles": profiles})
    export(out, assessment)
    if assessment['complete']:
        additional_reports(root, cfg, task_rows, out)
    csv_write(out / "summary.csv", summary_rows(result))
    matrix = profile_matrix(profiles, cfg["systems"]) if assessment['complete'] else []
    csv_write(out / "profile_matrix.csv", matrix)
    text = render_report(result, matrix) if assessment['complete'] else "Incomplete evaluation. Full-cohort accuracy is unavailable.\n"
    text += '\n' + coverage_text(assessment)
    (out / "report.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    print(f"Report and CSV files: {out}")
    return out


from pathlib import Path


def coverage_report(root, cfg, output=None):
    data = read(root / cfg["coverage"])
    names = {"S01":"synthphonia", "S02":"merlin", "S03":"prose", "S06":"crossbeam", "S08":"bustle"}
    rows = []
    for system in cfg["systems"]:
        records = [r for r in data["eligibility"]["records"] if names[r["system"]] == system and r["task_id"] in cfg["task_ids"]]
        eligible = sum(r["eligible_frozen_program"] for r in records)
        rows.append({"system": system, "tasks": len(records), "raw_frozen": sum(r["raw_status"] == "frozen" for r in records), "eligible_frozen": eligible, "coverage": eligible/len(records)})
    out = new_run(root, "coverage", output)
    write(out / "summary.json", {"experiment":cfg["id"], "systems":rows})
    csv_write(out / "summary.csv", rows)
    for row in rows:
        print(f'{row["system"]:<20} {row["eligible_frozen"]}/{row["tasks"]}  {row["coverage"]:.2%}')
    print(out)
    return out


def additional_reports(root, cfg, task_rows, out):
    tasks = tasks_for(root, cfg)
    index = {(r["system"], r["task_id"], r["suite"]):r for r in task_rows}
    sources = {tid: " / ".join(sorted(t["collections"])) for tid,t in tasks.items()}
    source_rows, sensitivity, paired = [], [], []
    for system in cfg["systems"]:
        for suite in ["heldout", "behavioral"]:
            source_means = []
            for source in sorted(set(sources.values())):
                rows = [index[system,tid,suite] for tid in tasks if sources[tid] == source]
                macro = sum(r["accuracy"] for r in rows)/len(rows)
                source_means.append(macro)
                source_rows.append({"system":system, "suite":suite, "source":source, "tasks":len(rows), "macro":macro, "correct":sum(r["correct"] for r in rows), "cases":sum(r["cases"] for r in rows)})
                remaining = [index[system,tid,suite] for tid in tasks if sources[tid] != source]
                if remaining:
                    sensitivity.append({"system":system, "suite":suite, "analysis":"exclude_source", "source":source, "tasks":len(remaining), "macro":sum(r["accuracy"] for r in remaining)/len(remaining)})
            sensitivity.append({"system":system, "suite":suite, "analysis":"equal_source_weight", "source":"all", "tasks":len(tasks), "macro":sum(source_means)/len(source_means)})
    for i, first in enumerate(cfg["systems"]):
        for second in cfg["systems"][i+1:]:
            for suite in ["heldout", "behavioral"]:
                differences = [index[first,tid,suite]["accuracy"] - index[second,tid,suite]["accuracy"] for tid in tasks]
                paired.append({"first":first, "second":second, "suite":suite, "tasks":len(tasks), "macro_difference":sum(differences)/len(differences), "first_better":sum(d>0 for d in differences), "first_worse":sum(d<0 for d in differences), "ties":sum(d==0 for d in differences)})
    csv_write(out / "sources.csv", source_rows)
    csv_write(out / "sensitivity.csv", sensitivity)
    csv_write(out / "paired.csv", paired)

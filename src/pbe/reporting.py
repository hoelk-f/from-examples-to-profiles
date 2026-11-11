def profile_matrix(profiles, systems):
    grouped = {}
    for row in profiles:
        if row["profile_kind"] != "taxonomy" or row["system"] not in systems:
            continue
        key = tuple(row[k] for k in ["dimension", "regime_family", "regime", "expectation"])
        group = grouped.setdefault(key, {})
        if row["system"] in group:
            raise ValueError("Duplicate profile cell: " + str(key))
        group[row["system"]] = row
    dimension_order = {"Value": 0, "Representation": 1, "Structure": 2, "Schema": 3}
    family_order = {"construction_intent": 0, "contract_conformance": 1, "observed_range_position": 2, "partition_location": 3}
    expectation_order = {"Exact Output": 0, "Invariance": 1, "Equivariance": 2}
    ordered = sorted(grouped, key=lambda k: (dimension_order.get(k[0], 99), k[0], family_order.get(k[1], 99), k[1], k[2], expectation_order.get(k[3], 99), k[3]))
    rows = []
    for key in ordered:
        group = grouped[key]
        if set(group) != set(systems):
            raise ValueError("Incomplete system coverage for profile cell: " + str(key))
        coverage = {(r["tasks"], r["cases"]) for r in group.values()}
        if len(coverage) != 1:
            raise ValueError("Unequal system coverage for profile cell: " + str(key))
        tasks, checks = coverage.pop()
        rows.append({"dimension": key[0], "regime_family": key[1], "regime": key[2], "expectation": key[3],
                     "tasks": tasks, "checks": checks, **{system: group[system]["macro"] for system in systems}})
    return rows


def summary_rows(result):
    rows = []
    for system in result["systems"]:
        heldout, behavior = system["heldout"], system["behavioral"]
        row = {"system": system["system"], "heldout_macro": heldout["macro"], "behavioral_macro": behavior["macro"],
               "heldout_full": heldout["fully_passing_tasks"], "behavioral_full": behavior["fully_passing_tasks"], "tasks": result["task_count"]}
        for name, metric in [("heldout", heldout), ("behavioral", behavior)]:
            row[name + "_tasks"] = metric["tasks"]
            row[name + "_full_rate"] = metric["fully_passing_tasks"] / metric["tasks"] if metric["tasks"] and metric.get("complete", True) else None
        rows.append(row)
    return rows


def percent(value):
    return "n/a" if value is None else f"{value:.2%}"


def table(headers, rows, left_columns=1):
    widths = [max(len(header), *(len(row[i]) for row in rows)) for i, header in enumerate(headers)]
    def line(row):
        return "  ".join(value.ljust(width) if i < left_columns else value.rjust(width)
                         for i, (value, width) in enumerate(zip(row, widths))).rstrip()
    return "\n".join([line(headers), line(["-" * width for width in widths]), *(line(row) for row in rows)])


def render_report(result, matrix):
    systems = [row["system"] for row in result["systems"]]
    parts = ["Behavioral profile matrix", "Dimension x Test regime x Expectation; mean per-task assertion pass rate (%).",
             "Tasks and checks show coverage per system. Rows overlap; counts must not be added."]
    if matrix:
        rows = [[r["dimension"], r["regime"], r["expectation"], str(r["tasks"]), str(r["checks"]),
                 *(percent(r[system]) for system in systems)] for r in matrix]
        parts += [table(["Dimension", "Test regime", "Expectation", "Tasks", "Checks", *systems], rows, left_columns=3)]
    else:
        parts += ["No behavioral profile cells were tested for this selection."]
    parts += ["Only tested cells are shown. Uncovered conditions are not passes or failures.",
              "Exact Output: required answer. Invariance: unchanged output. Equivariance: prescribed output change.",
              "", "Overall summary (secondary)",
              "Avg = mean of per-task exact-output accuracy. All-pass = tasks passing every test in that suite."]
    rows = []
    for r in summary_rows(result):
        all_pass = [f'{r[suite + "_full"]}/{r[suite + "_tasks"]} ({percent(r[suite + "_full_rate"])})'
                    for suite in ["heldout", "behavioral"]]
        rows.append([r["system"], percent(r["heldout_macro"]), percent(r["behavioral_macro"]), *all_pass])
    parts += [table(["System", "Held-out avg", "Behavior avg", "Held-out all-pass", "Behavior all-pass"], rows),
              "Partly correct tasks contribute to Avg, but not to the all-pass count."]
    return "\n".join(parts) + "\n"

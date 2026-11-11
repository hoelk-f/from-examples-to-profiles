# From Examples to Profiles

Code, data and literature evidence for the behavioral evaluation of PBE programs. The main comparison contains 168 tasks, 3,410 holdout inputs and 5,143 targeted inputs. It covers five classical systems and four LLM conditions with five repetitions each.

## Reproduce the reported results

Use Python 3.12 on Linux. Run from this checkout and install it in editable mode.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
reproduce verify
reproduce generate
reproduce analyze --output runs/results
```

These commands check file hashes and reference selectors, regenerate the targeted, random and program-selection inputs, and recompute the results from recorded program outputs. They need neither Docker nor an API key. Choose a new output directory for each analysis.

| Result | File in `runs/results/` |
| --- | --- |
| Holdout and behavioral accuracy, run SDs, additional failing tasks | `main.csv` |
| Six operator scores | `operators.csv` |
| Individual profile cells and comparison counts | `profiles.csv`, `profile_counts.json` |
| Equal operator rates versus local profile cells, with controls and examples | `operator_profile_counts.csv`, `operator_profile_pairs.csv`, `operator_profile_examples.csv` |
| Jaccard overlap and common failure examples | `overlap.csv`, `shared_failure_outputs.csv` |
| Matched-budget random comparison, draw SDs | `random.csv` |
| Task-cluster BCa and percentile intervals | `intervals.csv` |
| Leave-one-source-out checks and run/draw values | `leave_source_out.csv`, `variation.json` |
| Requirement-based program selection, scenarios and tie control | `selection.csv`, `selection_scenarios.csv`, `selection.json` |
| Exploratory sensitivity to 1–5 demonstrations | `sensitivity.csv` |
| Agreement with the recorded study | `validation.json` |

Expected selection accuracies are **78.6376%, 95.9946%, 96.9233%, 96.9233%** for holdout, overall behavioral, operator and profile selection. The profile-minus-overall difference is **0.9286 percentage points**, with a 95% BCa interval of **[0.4051, 1.9175]**. Validation also checks the main results, all 117 main/random intervals, 2,990 selection decisions and sensitivity results on eight tasks. Tables and figures can be recreated from the exported CSV files.

The local operator analysis restricts checks to one operator before grouping them into taxonomy cells. It compares programs from different conditions on the same task, using exact fractions for rate equality. With both programs fully passing holdout, S01 has different local profiles on **2 of 146** comparable tasks (T057, T092). V01–V05 have no such cases. Controls cover the first repetition, classical programs, all eligible programs, exact-output cells and unique-input weighting. Splitting S01 by insertion side also distinguishes every positive pair. These descriptive results do not establish superiority of the full taxonomy. Full local cells are exported in `operator_local_profiles.csv`.

Accuracy columns ending in `_pct` are percentages, `_pp` are percentage points. Random-comparison columns are numbers of tasks. SDs use the sample definition. Main SDs describe synthesis repetitions. Random SDs describe ten draws after averaging the synthesis repetitions. An empty SD means one run, not zero variability. Empty BCa bounds indicate an uninformative constant task vector. The intervals resample tasks jointly, keeping conditions, repetitions and draws together, with 20,000 resamples.

For the full profile of one program, including individual checks, applicability and assessment status:

```bash
reproduce profile --condition merlin --task T156 --output runs/profile-T156
```

## Execute the frozen programs again

Use Linux x86-64 and Docker. Download the pinned images and PROSE runtime from [release v1.0.0](https://github.com/hoelk-f/from-examples-to-profiles/releases/tag/v1.0.0). The 3.18 GB archive is split into two files, each below 2 GiB. `SHA256SUMS` covers both parts and the assembled archive. Allow at least 20 GB free disk space for download, extraction and Docker import, and 8 GB RAM when using two workers. Run these commands from the checkout after the Python installation above.

```bash
runtime_release=https://github.com/hoelk-f/from-examples-to-profiles/releases/download/v1.0.0
runtime_archive=from-examples-to-profiles-runtimes.tar.gz
mkdir -p .cache/runtime-download
for file in SHA256SUMS "$runtime_archive.part01" "$runtime_archive.part02"
do
    curl -fL --retry 3 "$runtime_release/$file" -o ".cache/runtime-download/$file"
done
(
    cd .cache/runtime-download
    cat "$runtime_archive.part01" "$runtime_archive.part02" > "$runtime_archive"
    sha256sum -c SHA256SUMS
)
```

Continue only if all three checksum checks report `OK`. Extraction creates the two `runtime-bundles/` directories used by the loader.

```bash
tar -xzf .cache/runtime-download/from-examples-to-profiles-runtimes.tar.gz
reproduce runtime load
reproduce evaluate --suite main --task T156 --output runs/smoke
for suite in main random selection sensitivity
do
    reproduce evaluate --suite "$suite" --output runs/reexecuted --workers 2
done
reproduce analyze --source runs/reexecuted --output runs/reexecuted-results
```

The loader supports both classic and containerd image stores. Where an archive index omits config-pinned images, it builds a temporary compatible index and verifies the unchanged image configurations and layers. The downloaded archives and their checksums remain unchanged.

Each execution checks the demonstrations and compares every test output with the recorded output. Add `--resume` to continue completed program jobs with the same options. An interrupted individual job requires inspection. Full reexecution is substantially slower than recomputing the results. Outputs never replace the frozen records.

## Repeat synthesis

Synthesis uses the original demonstrations, prompts, grammars, search limits and runtime pins. Held-out labels and reference selectors are not passed to synthesis adapters. Model answers are replayed by default.

```bash
reproduce synthesize --condition synthphonia --output runs/synthphonia
reproduce synthesize --condition direct-python/gpt-oss-120b --repeat 1 --output runs/direct-r1
reproduce synthesize --condition hysynth-string/qwen3.8-27b --repeat 1 --output runs/hysynth-r1
reproduce evaluate --suite main --programs runs/direct-r1/programs.json --output runs/direct-r1-eval
```

Other classical condition names are `merlin`, `prose`, `crossbeam`, `bustle`. Both LLM systems support `gpt-oss-120b` and `qwen3.8-27b`. Use repeats 1–5 for the main LLM experiment. Add `--task T002` for a small run. For sensitivity, add `--suite sensitivity --examples N`, with N from 1 to 5, five direct-generation repetitions and three HySynth repetitions. `scripts/synthesize_all.sh` runs either complete design sequentially.

To evaluate and analyze a complete new synthesis run with the published test inputs:

```bash
bash scripts/synthesize_all.sh main runs/new-main
bash scripts/synthesize_all.sh sensitivity runs/new-sensitivity
for suite in main random selection
do
    reproduce evaluate --suite "$suite" --programs runs/new-main --output runs/new-evaluation
done
reproduce evaluate --suite sensitivity --programs runs/new-sensitivity --output runs/new-evaluation
reproduce analyze --source runs/new-evaluation --output runs/new-results
```

Directory input checks that all 4,600 main or 1,155 sensitivity attempts finished, including unsuccessful attempts. HySynth search memory exhaustion is recorded as `out_of_memory`, preserves its logs, and allows the next task to proceed. Infrastructure and unclassified errors still stop the run. Resume with the same `synthesize` options and `--resume`, or append `--resume` to `synthesize_all.sh`. Completed failures are not retried.

New-program analysis recalculates selections and common cohorts. The main comparison uses the published 168-task evaluation scope, retaining only tasks with eligible programs in all conditions and repetitions. Sensitivity uses the common cohort across all example counts. `main_cohort.json`, `sensitivity_cohort.json`, `validation.json` and `reference_differences.csv` identify cohort and numerical changes. A partial single-condition run supports evaluation, but not the complete comparative analysis.

To request fresh model answers, copy `experiments/providers.json`, configure an accessible endpoint and export the named API-key environment variable. Add `--live --provider path/to/providers.json`. This sends paid or quota-consuming requests, one per direct task or ten per HySynth task. The recorded endpoint requires institutional access. A different provider or model version is a new experimental condition. Fresh responses and time-limited search can change the selected programs and the common cohort. Only the frozen-record workflow is expected to recover the reported values exactly. Evaluation of new programs writes per-task accuracy without asserting agreement with the study.

## Contents

`data/` contains task contracts, source provenance, fixed splits, test inputs, grammars, prompts and program files. `records/` contains compressed observations and program indexes. `reference/` holds numerical checks, not inputs to the metric calculations. `src/pbe/` implements test generation, two reference selectors, scoring and isolated runtime adapters. `src/pbe_artifact/` provides the reproduction commands. Runtime pins and upstream provenance are in `runtimes/`. The literature protocol and evidence are in [literature/README.md](literature/README.md).

The source-selection audit is in `data/provenance/curation.json`. It records three exclusions from 285 tasks and two subsequent merges, yielding 280 tasks. Initial eligibility and holdout screening retained 184 tasks. `records/main_missing.json` explains the later exclusions that leave the common 168-task set. Earlier historical task IDs are mapped to the current IDs. Contracts and literature judgments are supplied as recorded decisions, not inferred automatically from demonstrations.

No manuscript files or credentials are included. Third-party materials retain their original licenses and attribution. See `NOTICE`.

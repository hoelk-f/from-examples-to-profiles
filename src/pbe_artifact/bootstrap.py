from collections import defaultdict
import numpy as np
import warnings
from scipy.stats import bootstrap, DegenerateDataWarning
from .common import ORDER
REPEATS = {c: ([1] if i < 5 else list(range(1, 6))) for i,c in enumerate(ORDER)}


class IncompleteData(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise IncompleteData(message)

def build_vectors(main_rows, random_rows, conditions, tids):
    main = {(x["condition"], x["program_repeat"], x["task_id"]): x for x in main_rows}
    random = {(x["condition"], x["program_repeat"], x["task_id"], x["generator"], x["sampling_repeat"]): x
              for x in random_rows}
    vectors, metadata, variation = [], [], []
    n = len(tids)
    for c in conditions:
        reps = REPEATS[c]
        h = np.array([[main[c, r, t]["holdout_accuracy"] for t in tids] for r in reps])
        b = np.array([[main[c, r, t]["behavioral_accuracy"] for t in tids] for r in reps])
        hf = np.array([[main[c, r, t]["holdout_fully_passed"] for t in tids] for r in reps], dtype=float)
        tf = np.array([[main[c, r, t]["targeted_failed"] for t in tids] for r in reps], dtype=float)
        targeted = hf * tf
        for metric, values in [
            ("holdout_accuracy", h), ("behavioral_accuracy", b),
            ("holdout_minus_behavioral_accuracy", h-b),
            ("fully_passing_holdout", hf), ("targeted_additional_failures", targeted),
        ]:
            vectors.append(values.mean(axis=0))
            metadata.append(dict(condition=c, metric=metric, generator="", nonzero_tasks=int(np.count_nonzero(values.mean(axis=0)))))
            run_means = values.mean(axis=1)
            variation.append(dict(condition=c, metric=metric, generator="",
                                  synthesis_sd_pp=float(np.std(run_means, ddof=1)*100) if len(reps)>1 else None,
                                  draw_sd_pp=None, run_values_pp=(run_means*100).tolist(), draw_values_pp=[]))
        for g in ["nominal", "broad"]:
            rf = np.array([[[random[c, r, t, g, d]["random_failed"] for t in tids] for r in reps]
                           for d in range(1, 11)], dtype=float)
            additional = rf * hf[None, :, :]
            delta = additional - targeted[None, :, :]
            for metric, values in [
                ("random_additional_failures", additional), ("random_minus_targeted", delta),
                ("random_only_additional_failures", additional * (1-tf[None, :, :])),
                ("targeted_only_additional_failures", targeted[None, :, :] * (1-rf)),
            ]:
                vector = values.mean(axis=(0, 1))
                vectors.append(vector)
                discordant = int(np.count_nonzero(np.any(delta != 0, axis=(0, 1))))
                metadata.append(dict(condition=c, metric=metric, generator=g,
                                     nonzero_tasks=int(np.count_nonzero(vector)),
                                     discordant_tasks=discordant if metric == "random_minus_targeted" else None))
                run_means = values.mean(axis=(0, 2))
                draw_means = values.mean(axis=(1, 2))
                variation.append(dict(condition=c, metric=metric, generator=g,
                                      synthesis_sd_pp=float(np.std(run_means, ddof=1)*100) if len(reps)>1 else None,
                                      draw_sd_pp=float(np.std(draw_means, ddof=1)*100),
                                      run_values_pp=(run_means*100).tolist(), draw_values_pp=(draw_means*100).tolist()))
    return np.array(vectors), metadata, variation

def bootstrap_vectors(values, resamples=20000, seed=20261103):
    require(values.ndim == 2 and values.shape[1] >= 2 and np.isfinite(values).all(),
            "Bootstrap needs finite task vectors.")
    varying = np.ptp(values, axis=1) > 1e-14
    distribution = np.repeat(values.mean(axis=1)[:, None], resamples, axis=1)
    lower, upper = np.full(values.shape[0], np.nan), np.full(values.shape[0], np.nan)
    warning_messages = []
    if varying.any():
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DegenerateDataWarning)
            result = bootstrap(
                (values[varying],), np.mean, axis=-1, vectorized=True, paired=True,
                n_resamples=resamples, batch=128, confidence_level=0.95,
                method="BCa", rng=np.random.default_rng(seed),
            )
        distribution[varying] = result.bootstrap_distribution
        lower[varying], upper[varying] = result.confidence_interval
        warning_messages = [str(w.message) for w in caught]
    percentile = np.quantile(distribution, [0.025, 0.975], axis=1, method="linear")
    return lower, upper, percentile, distribution, warning_messages

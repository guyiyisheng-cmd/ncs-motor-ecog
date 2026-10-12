"""One deterministic hierarchical calculation, two explicitly named beta estimands."""
from __future__ import annotations
import hashlib
import numpy as np
from .core import MethodError, beta_from_events, pac_from_events, association, conditional_range
from .data import Subject


def complete_median(values) -> float:
    """Never silently reduce a five-action summary to fewer actions."""
    x = np.asarray(values, dtype=float)
    return float(np.median(x)) if len(x) and np.isfinite(x).all() else float("nan")


def indices_for(s: Subject, action: str | None, condition: str, round_counts) -> np.ndarray:
    indices = []
    for r, count in zip(s.rounds, round_counts):
        for _ in range(int(count)):
            for a in (s.actions if action is None else [action]):
                indices.append(s.lookup[(r, a, condition)])
    return np.asarray(indices, int)


def estimate(s: Subject, cfg: dict, counts, keep_channels: bool = False):
    """All calculations use the same sampled complete rounds for both outcomes."""
    flat: dict[tuple, float] = {}
    channel_rows, pair_rows, combined_rows = [], [], []
    grids = {name: list(range(s.pac_delta.shape[2])) if spec == "all" else spec
             for name, spec in cfg["pac_grids"].items()}
    # All-action summaries kept separate from action-specific contrasts.
    for condition in s.conditions:
        ix = indices_for(s, None, condition, counts)
        b = beta_from_events(s.beta, s.times, ix, cfg["task"], cfg["baseline"], cfg["include_right_endpoint"])
        for beta_name in ("original", "same_scale", "baseline_level"):
            flat[("combined", condition, beta_name, "median")] = float(np.median(b[beta_name]))
        if keep_channels:
            for j, ch in enumerate(s.channels):
                combined_rows.append({"subject": s.subject, "record": s.record, "channel": ch, "condition": condition,
                                      **{k: float(v[j]) for k, v in b.items()}})
    for action in s.actions:
        cond = {}
        for condition in s.conditions:
            ix = indices_for(s, action, condition, counts)
            b = beta_from_events(s.beta, s.times, ix, cfg["task"], cfg["baseline"], cfg["include_right_endpoint"])
            p = {grid: pac_from_events(s.pac_delta, ix, bands, cfg["pac_quantile"]) for grid, bands in grids.items()}
            cov = np.median(s.covariate[ix], axis=0) if s.covariate is not None else None
            cond[condition] = (b, p, cov)
            for name, vector in b.items():
                flat[("effect", action, condition, "beta_" + name)] = float(np.median(vector))
            for name, vector in p.items():
                flat[("effect", action, condition, "pac_" + name)] = float(np.median(vector))
            if keep_channels:
                for j, ch in enumerate(s.channels):
                    row = {"subject": s.subject, "record": s.record, "action": action, "condition": condition, "channel": ch,
                           **{"beta_" + k: float(v[j]) for k, v in b.items()},
                           **{"pac_" + k: float(v[j]) for k, v in p.items()}}
                    row["amplitude_power_db"] = float(cov[j]) if cov is not None else np.nan
                    channel_rows.append(row)
        ref, cmp = (cond[c] for c in s.conditions)
        db = {key: cmp[0][key] - ref[0][key] for key in ref[0]}
        dp = {key: cmp[1][key] - ref[1][key] for key in ref[1]}
        dc = cmp[2] - ref[2] if ref[2] is not None else None
        for name, vector in db.items():
            flat[("effect", action, "comparison_minus_reference", "beta_" + name)] = float(np.median(vector))
        for name, vector in dp.items():
            flat[("effect", action, "comparison_minus_reference", "pac_" + name)] = float(np.median(vector))
        if keep_channels:
            for j, ch in enumerate(s.channels):
                pair_rows.append({"subject": s.subject, "record": s.record, "action": action, "channel": ch,
                                  **{"delta_beta_" + k: float(v[j]) for k, v in db.items()},
                                  **{"delta_pac_" + k: float(v[j]) for k, v in dp.items()},
                                  "delta_amplitude_power_db": float(dc[j]) if dc is not None else np.nan})
        for contrast, values in list(cond.items()) + [("comparison_minus_reference", (db, dp, dc))]:
            b, p, cov = values
            for bname in ("original", "same_scale"):
                for grid in grids:
                    stats = association(b[bname], p[grid], cov)
                    for metric, value in stats.items():
                        flat[("association", action, contrast, bname, grid, metric)] = value
    for contrast in list(s.conditions) + ["comparison_minus_reference"]:
        for bname in ("original", "same_scale"):
            for grid in grids:
                for metric in ("rho", "slope", "partial_rho"):
                    flat[("subject", contrast, bname, grid, metric)] = complete_median(
                        [flat[("association", action, contrast, bname, grid, metric)] for action in s.actions])
    return flat, channel_rows, pair_rows, combined_rows


def bootstrap_subject(s: Subject, cfg: dict):
    nround = len(s.rounds)
    original, channel_rows, pair_rows, combined_rows = estimate(s, cfg, np.ones(nround, int), True)
    if s.boot_indices is not None:
        draws = s.boot_indices
        draw_origin = "source_provided_indices"
    else:
        # Record-specific RNG keeps subject processing order from changing results.
        entropy = [cfg["seed"], int.from_bytes(hashlib.sha256((s.subject + ":" + s.record).encode()).digest()[:4], "big")]
        rng = np.random.default_rng(np.random.SeedSequence(entropy))
        draws = rng.integers(0, nround, size=(cfg["n_resamples"], nround))
        draw_origin = "generated_record_specific_seed_sequence"
    keys = list(original)
    samples = np.empty((len(draws), len(keys)))
    # Nonlinear medians depend on counts, not the order in a with-replacement draw.
    # At most 126/462 distinct count patterns for 5/6 rounds; avoids redundant work.
    cache = {}
    for i, draw in enumerate(draws):
        counts = tuple(np.bincount(draw, minlength=nround))
        if counts not in cache:
            current = estimate(s, cfg, counts)[0]
            if list(current) != keys:
                raise MethodError("statistic index changed during bootstrap")
            cache[counts] = np.array([current[k] for k in keys])
        samples[i] = cache[counts]
    rows = []
    for col, key in enumerate(keys):
        ci = conditional_range(samples[:, col], cfg.get("min_valid_fraction", 0.95))
        if key[0] == "combined":
            category, contrast, beta_name, metric = key
            row = {"category": category, "action": "all_actions", "contrast": contrast, "beta_definition": beta_name,
                   "pac_grid": "not_applicable", "metric": metric}
        elif key[0] == "effect":
            category, action, contrast, metric = key
            row = {"category": category, "action": action, "contrast": contrast,
                   "beta_definition": "in_metric_name", "pac_grid": "in_metric_name", "metric": metric}
        elif key[0] == "association":
            category, action, contrast, bname, grid, metric = key
            row = {"category": category, "action": action, "contrast": contrast, "beta_definition": bname, "pac_grid": grid, "metric": metric}
        else:
            category, contrast, bname, grid, metric = key
            row = {"category": category, "action": "median_of_action_specific_statistics", "contrast": contrast,
                   "beta_definition": bname, "pac_grid": grid, "metric": metric}
        value = original[key]
        rows.append({"subject": s.subject, "record": s.record, **row, "estimate": value, **ci,
                     "point_status": "estimated" if np.isfinite(value) else "undefined_or_unavailable",
                     "range_status": "estimated" if np.isfinite(ci["lower"]) else "insufficient_defined_resamples",
                     "n_channels": len(s.channels), "n_rounds": nround,
                     "range_scope": "conditional_on_observed_patient_channels_actions"})
    return rows, channel_rows, pair_rows, combined_rows, draws, {
        "subject": s.subject, "record": s.record, "draw_origin": draw_origin,
        "unique_round_multisets": len(cache), "n_events": len(s.event_ids),
        "n_channels": len(s.channels), "n_actions": len(s.actions), "n_rounds": nround,
        "covariate_available": s.covariate is not None}

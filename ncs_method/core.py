"""Numerical definitions, deliberately independent of a PAC library backend.

All inferential summaries preserve subject/action/channel identity. Array tests
establish implementation properties, not physiological or clinical validity.
"""
from __future__ import annotations

import numpy as np


class MethodError(ValueError):
    """A data contract or an explicitly declared estimator assumption failed."""


def finite_array(value, name: str) -> np.ndarray:
    a = np.asarray(value, dtype=np.float64)
    if a.size == 0 or not np.isfinite(a).all():
        raise MethodError(f"{name}: empty or nonfinite values; do not replace missing data with zero")
    return a


def mi_from_phase_amplitude(phase, amplitude, n_bins: int = 18) -> np.ndarray:
    """Tort-style MI, one independent estimate per leading-index combination.

    Inputs have identical shape (..., samples). Counts are NEVER pooled across
    windows or phase frequencies. Empty phase bins and zero total amplitude
    are undefined and raise an error rather than being silently imputed.
    Positive amplitude rescaling leaves MI invariant.
    """
    p = finite_array(phase, "phase")
    a = finite_array(amplitude, "amplitude")
    if p.shape != a.shape or p.ndim < 1 or n_bins < 2:
        raise MethodError("phase/amplitude shapes must match; samples are last; n_bins >= 2")
    if (a < 0).any():
        raise MethodError("amplitude must be nonnegative")
    # (-pi, pi] conventions do not affect the circular variable; bins are fixed.
    index = np.floor(((p + np.pi) % (2 * np.pi)) * n_bins / (2 * np.pi)).astype(int)
    index = np.minimum(index, n_bins - 1)
    means = []
    for k in range(n_bins):
        selected = index == k
        count = selected.sum(axis=-1)
        if (count == 0).any():
            raise MethodError("empty phase bin: the requested MI is undefined under this contract")
        means.append(np.where(selected, a, 0.0).sum(axis=-1) / count)
    means = np.stack(means, axis=-1)
    total = means.sum(axis=-1, keepdims=True)
    if (total <= 0).any():
        raise MethodError("zero total phase-bin amplitude")
    prob = means / total
    logprob = np.zeros_like(prob)
    np.log(prob, out=logprob, where=prob > 0)
    mi = np.sum(prob * (logprob + np.log(n_bins)), axis=-1) / np.log(n_bins)
    # Only remove machine round-off at the mathematical endpoints.
    return np.clip(mi, 0.0, 1.0)


def phase_bin_mi_reference(phase, amplitude, n_bins: int = 18) -> float:
    """Slow scalar reference implementation for tests (one window only)."""
    p, a = finite_array(phase, "phase"), finite_array(amplitude, "amplitude")
    if p.ndim != 1 or p.shape != a.shape or n_bins < 2 or (a < 0).any():
        raise MethodError("reference MI expects one valid 1D window")
    means = []
    angles = ((p + np.pi) % (2 * np.pi)) - np.pi
    for k in range(n_bins):
        lo = -np.pi + 2 * np.pi * k / n_bins
        hi = -np.pi + 2 * np.pi * (k + 1) / n_bins
        bucket = a[(angles >= lo) & (angles < hi)]
        if len(bucket) == 0:
            raise MethodError("reference empty phase bin")
        means.append(float(sum(bucket) / len(bucket)))
    total = sum(means)
    if total <= 0:
        raise MethodError("reference zero amplitude")
    probability = [x / total for x in means]
    return float(sum(x * np.log(x * n_bins) for x in probability if x > 0) / np.log(n_bins))


def time_mask(times, interval, include_right: bool) -> np.ndarray:
    t = finite_array(times, "times")
    if t.ndim != 1 or len(interval) != 2 or interval[0] >= interval[1]:
        raise MethodError("times must be 1D; interval must be increasing")
    if not (np.diff(t) > 0).all():
        raise MethodError("time points must be strictly increasing")
    mask = (t >= interval[0]) & ((t <= interval[1]) if include_right else (t < interval[1]))
    if not mask.any():
        raise MethodError("empty time interval")
    return mask


def beta_from_events(beta_db, times, event_indices, task=(0.0, 5.0),
                     baseline=(-2.0, 0.0), include_right=True) -> dict[str, np.ndarray]:
    """Event median at each time -> time mean, separately for task/baseline.

    beta_db is (events, channels, time), already source-preprocessed dB.
    `original` and `same_scale` are different estimands, not right/wrong labels.
    include_right=True deliberately preserves V02's shared t=0 endpoint.
    """
    b = np.asarray(beta_db, dtype=np.float64)
    ix = np.asarray(event_indices, dtype=int)
    if b.ndim != 3 or ix.ndim != 1 or ix.size == 0 or b.shape[-1] != len(times):
        raise MethodError("invalid beta/event/time shapes")
    if (ix < 0).any() or (ix >= len(b)).any():
        raise MethodError("invalid event index")
    curve = np.median(b[ix], axis=0)
    tm = time_mask(times, task, include_right)
    bm = time_mask(times, baseline, include_right)
    original = np.mean(curve[:, tm], axis=-1)
    baseline_level = np.mean(curve[:, bm], axis=-1)
    return {"original": original, "baseline_level": baseline_level,
            "same_scale": original - baseline_level}


def pac_event_contrast(task_mi, baseline_mi) -> np.ndarray:
    """(E,C,W,A,P) -> (E,C,A,P); median windows, then task minus baseline."""
    task = finite_array(task_mi, "task_mi")
    base = finite_array(baseline_mi, "baseline_mi")
    if task.ndim != 5 or base.ndim != 5:
        raise MethodError("PAC inputs must be (event,channel,window,amplitude,phase)")
    if task.shape[:2] + task.shape[3:] != base.shape[:2] + base.shape[3:]:
        raise MethodError("task/base MI non-window axes differ")
    if (task < -1e-12).any() or (base < -1e-12).any() or (task > 1 + 1e-12).any() or (base > 1 + 1e-12).any():
        raise MethodError("unsubtracted normalized MI must lie in [0,1]")
    return np.median(task, axis=2) - np.median(base, axis=2)


def pac_window_median_contrast(task_median, baseline_median) -> np.ndarray:
    """Explicit E,C,A,P interface for source window medians, without fake windows."""
    task = finite_array(task_median, "pac_task_window_median")
    base = finite_array(baseline_median, "pac_baseline_window_median")
    if task.ndim != 4 or task.shape != base.shape:
        raise MethodError("PAC window-median grids must have matching E,C,A,P axes")
    if any((x < -1e-12).any() or (x > 1 + 1e-12).any() for x in (task, base)):
        raise MethodError("unsubtracted window-median MI must lie in [0,1]")
    return task - base


def pac_from_events(event_delta, event_indices, amp_indices, quantile=0.95) -> np.ndarray:
    """Cellwise event median FIRST, frequency-grid quantile SECOND."""
    d = np.asarray(event_delta, dtype=np.float64)
    ix = np.asarray(event_indices, dtype=int)
    bands = np.asarray(amp_indices, dtype=int)
    if d.ndim != 4 or ix.size == 0 or bands.size == 0:
        raise MethodError("PAC contrasts must be (E,C,A,P) with nonempty indices")
    if len(set(bands.tolist())) != len(bands) or (bands < 0).any() or (bands >= d.shape[2]).any():
        raise MethodError("invalid or duplicated amplitude index")
    if (ix < 0).any() or (ix >= d.shape[0]).any() or not 0 < quantile <= 1:
        raise MethodError("invalid event index or quantile")
    cells = np.median(d[ix], axis=0)[:, bands, :]
    return np.quantile(cells.reshape(cells.shape[0], -1), quantile, axis=1, method="linear")


def average_ranks(values) -> np.ndarray:
    """One-based midranks with exact ties, no SciPy dependency."""
    x = finite_array(values, "rank values")
    if x.ndim != 1:
        raise MethodError("ranks require a vector")
    order = np.argsort(x, kind="mergesort")
    sorted_x = x[order]
    starts = np.r_[0, 1 + np.flatnonzero(sorted_x[1:] != sorted_x[:-1])]
    ends = np.r_[starts[1:], len(x)]
    ranks = np.empty(len(x), dtype=float)
    for start, end in zip(starts, ends):
        ranks[order[start:end]] = (start + 1 + end) / 2.0
    return ranks


def pearson(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.shape != y.shape or x.ndim != 1 or len(x) < 3:
        return float("nan")
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        return float("nan")
    xc, yc = x - x.mean(), y - y.mean()
    nx, ny = np.linalg.norm(xc), np.linalg.norm(yc)
    if nx == 0 or ny == 0:
        return float("nan")
    return float(np.clip(np.dot(xc / nx, yc / ny), -1, 1))


def association(x, y, covariate=None) -> dict[str, float]:
    """Descriptive rho/slope/partial-rho; no independent-channel p value."""
    x, y = finite_array(x, "x"), finite_array(y, "y")
    if x.ndim != 1 or x.shape != y.shape:
        raise MethodError("association requires matching vectors")
    rx, ry = average_ranks(x), average_ranks(y)
    rho = pearson(rx, ry)
    xc, yc = x - x.mean(), y - y.mean()
    denom = float(np.dot(xc, xc))
    slope = float(np.dot(xc, yc) / denom) if denom > 0 else float("nan")
    partial = float("nan")
    if covariate is not None:
        z = finite_array(covariate, "covariate")
        if z.shape != x.shape:
            raise MethodError("covariate shape differs")
        rz = average_ranks(z)
        design = np.column_stack([np.ones(len(x)), rz])
        if len(x) >= 4 and np.linalg.matrix_rank(design) == 2:
            ex = rx - design @ np.linalg.lstsq(design, rx, rcond=None)[0]
            ey = ry - design @ np.linalg.lstsq(design, ry, rcond=None)[0]
            # Exact rank collinearity must not create a numerical residual correlation.
            if np.linalg.norm(ex) > 1e-10 * np.linalg.norm(rx) and np.linalg.norm(ey) > 1e-10 * np.linalg.norm(ry):
                partial = pearson(ex, ey)
    return {"rho": rho, "slope": slope, "partial_rho": partial}


def conditional_range(values, min_valid_fraction=0.95) -> dict[str, float | int]:
    """Bootstrap percentiles conditional on the observed patients and channels."""
    a = np.asarray(values, dtype=float)
    good = np.isfinite(a)
    n = int(good.sum())
    if a.ndim != 1 or not len(a):
        raise MethodError("conditional range requires a nonempty vector")
    lo, hi = (np.quantile(a[good], [0.025, 0.975], method="linear")
              if n >= 2 and n / len(a) >= min_valid_fraction else (np.nan, np.nan))
    return {"lower": float(lo), "upper": float(hi), "n_valid": n, "n_resamples": len(a)}

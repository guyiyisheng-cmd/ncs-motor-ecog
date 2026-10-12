"""Explicit input contract. Does not guess the schema of the local NCS archive."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import re
import numpy as np
from .core import MethodError, finite_array, pac_event_contrast, pac_window_median_contrast, time_mask

TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")


def token(value: str, name: str) -> str:
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise MethodError(f"{name}: use a nonidentifying ASCII token, not a name or file path")
    return value


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise MethodError("JSON top level must be an object")
    return value


def resolve_input(value: str, config_dir: Path) -> Path:
    p = Path(value).expanduser()
    return (p if p.is_absolute() else config_dir / p).resolve(strict=True)


@dataclass
class Subject:
    subject: str
    record: str
    dataset_kind: str
    beta: np.ndarray
    times: np.ndarray
    pac_delta: np.ndarray
    channels: list[str]
    actions: list[str]
    conditions: tuple[str, str]
    rounds: list[str]
    event_ids: list[str]
    lookup: dict[tuple[str, str, str], int]
    amp_bands: np.ndarray
    phase_bands: np.ndarray
    covariate: np.ndarray | None
    boot_indices: np.ndarray | None
    input_paths: list[Path]


def load_subject(item: dict, config_dir: Path, config: dict) -> Subject:
    meta_path = resolve_input(item["metadata"], config_dir)
    array_path = resolve_input(item["arrays"], config_dir)
    m = read_json(meta_path)
    if m.get("schema") != "ncs-arrays-1":
        raise MethodError("metadata.schema must be ncs-arrays-1")
    if m.get("dataset_kind") not in ("clinical", "synthetic_software_test"):
        raise MethodError("dataset_kind must explicitly distinguish clinical from synthetic software tests")
    for flag in ("event_channel_alignment_reviewed", "source_array_provenance_reviewed"):
        if m.get(flag) is not True:
            raise MethodError(f"{flag} must have been checked against actual local sources")
    if m.get("mi_normalization") != "per_window_per_phase_bin_means":
        raise MethodError("MI normalization identity is not the required per-window/per-phase definition")
    if m.get("beta_unit") != "dB" or m.get("mi_unit") != "dimensionless":
        raise MethodError("explicit beta=dB, MI=dimensionless units required")
    conditions = tuple(config["conditions"])
    if conditions != tuple(m.get("conditions", [])) or len(conditions) != 2:
        raise MethodError("ordered conditions must agree: reference first, comparison second")
    actions = [token(x, "action") for x in m["actions"]]
    channels = [token(x, "channel") for x in m["channels"]]
    rounds = [token(x, "round") for x in m["rounds"]]
    if not actions or not channels or len(rounds) < 2:
        raise MethodError("nonempty actions/channels and at least two complete rounds are required")
    for values in (actions, channels, rounds):
        if len(values) != len(set(values)):
            raise MethodError("duplicate action/channel/round token")
    for c in conditions:
        token(c, "condition")
    event_ids, lookup = [], {}
    for i, event in enumerate(m["events"]):
        event_ids.append(token(event["event_id"], "event_id"))
        key = (event["round_id"], event["action"], event["condition"])
        if key in lookup:
            raise MethodError("duplicate round/action/condition event; do not guess which one is genuine")
        lookup[key] = i
    expected = {(r, a, c) for r in rounds for a in actions for c in conditions}
    if set(lookup) != expected or len(set(event_ids)) != len(event_ids):
        raise MethodError("round design is incomplete or event IDs are duplicated; no automatic event deletion")
    with np.load(array_path, allow_pickle=False) as z:
        form = m.get("pac_input_form", "window_arrays")
        if form not in ("window_arrays", "source_window_medians"):
            raise MethodError("unknown pac_input_form")
        pac_keys = (["pac_task_mi", "pac_baseline_mi"] if form == "window_arrays" else
                    ["pac_task_window_median", "pac_baseline_window_median"])
        required = ["beta_db", "times_s", "event_ids", "channel_ids"] + pac_keys
        if any(k not in z for k in required):
            raise MethodError("canonical NPZ missing required arrays; run the source adapter first")
        if z["event_ids"].tolist() != event_ids or z["channel_ids"].tolist() != channels:
            raise MethodError("NPZ event/channel IDs do not match metadata order")
        beta = finite_array(z["beta_db"], "beta_db")
        times = finite_array(z["times_s"], "times_s")
        task = finite_array(z[pac_keys[0]], pac_keys[0])
        base = finite_array(z[pac_keys[1]], pac_keys[1])
        cov = finite_array(z["amplitude_power_db"], "amplitude_power_db") if "amplitude_power_db" in z else None
        boot = np.array(z["bootstrap_indices"]) if "bootstrap_indices" in z else None
    ec = (len(event_ids), len(channels))
    if beta.ndim != 3 or beta.shape[:2] != ec or beta.shape[-1] != len(times):
        raise MethodError("beta dimensions differ from declared events/channels/time")
    if task.shape[:2] != ec or base.shape[:2] != ec:
        raise MethodError("MI dimensions differ from event/channel identifiers")
    if form == "window_arrays":
        if task.ndim != 5 or base.ndim != 5 or task.shape[2] != m.get("task_windows") or base.shape[2] != m.get("baseline_windows"):
            raise MethodError("actual PAC window counts do not match declared counts")
        delta = pac_event_contrast(task, base)
    else:
        if m.get("source_window_aggregation") != "median_over_windows_before_event_aggregation":
            raise MethodError("source window-median aggregation must be explicitly confirmed")
        for key in ("task_windows", "baseline_windows"):
            if type(m.get(key)) is not int or m[key] < 1:
                raise MethodError("declare original positive window counts, not virtual windows")
        delta = pac_window_median_contrast(task, base)
    amp, phase = np.asarray(m["amplitude_bands_hz"], float), np.asarray(m["phase_bands_hz"], float)
    for bands in (amp, phase):
        if bands.ndim != 2 or bands.shape[1] != 2 or not np.isfinite(bands).all() or not (bands[:, 1] > bands[:, 0]).all():
            raise MethodError("invalid frequency-band limits")
    if delta.shape[2:] != (len(amp), len(phase)):
        raise MethodError("MI frequency axes disagree with declared bands")
    if cov is not None:
        if cov.shape != ec or m.get("amplitude_power_unit") != "dB" or m.get("amplitude_power_aggregation") != "event_scalar_median_within_action_condition":
            raise MethodError("optional power covariate must be E,C dB with documented event-scalar aggregation")
    if boot is not None:
        if boot.dtype.kind not in "iu" or boot.shape != (config["n_resamples"], len(rounds)):
            raise MethodError("bootstrap_indices must be integer (n_resamples,n_rounds)")
        if (boot < 0).any() or (boot >= len(rounds)).any():
            raise MethodError("bootstrap index out of bounds")
    for name in ("task", "baseline"):
        time_mask(times, config[name], config["include_right_endpoint"])
    return Subject(token(m["subject"], "subject"), token(m["record"], "record"), m["dataset_kind"],
                   beta, times, delta, channels, actions, conditions, rounds,
                   event_ids, lookup, amp, phase, cov, boot, [meta_path, array_path])


def validate_config(c: dict) -> dict:
    required = {"schema", "conditions", "task", "baseline", "include_right_endpoint", "n_resamples", "seed", "pac_quantile", "pac_grids", "subjects", "method_reference"}
    if not required.issubset(c) or c["schema"] != "ncs-run-1":
        raise MethodError("invalid run configuration: see examples/config_template.json")
    if not isinstance(c["include_right_endpoint"], bool):
        raise MethodError("include_right_endpoint must be explicitly true or false")
    if isinstance(c["n_resamples"], bool) or not isinstance(c["n_resamples"], int) or not 20 <= c["n_resamples"] <= 100000:
        raise MethodError("n_resamples must be 20..100000; no silent lower-resolution run")
    if not isinstance(c["seed"], int) or c["seed"] < 0 or not 0 < c["pac_quantile"] <= 1:
        raise MethodError("invalid seed or quantile")
    if not c["subjects"] or not c["method_reference"]:
        raise MethodError("declare subjects and the implemented method reference")
    if not 0 < c.get("min_valid_fraction", 0.95) <= 1:
        raise MethodError("min_valid_fraction must be (0,1]")
    if not isinstance(c["pac_grids"], dict) or not c["pac_grids"]:
        raise MethodError("at least one declared PAC grid is required")
    if c.get("target_rho") is not None or c.get("target_p") is not None:
        raise MethodError("target numerical outcomes are not analysis configuration parameters")
    for label, indices in c["pac_grids"].items():
        token(label, "grid label")
        if indices != "all" and (not isinstance(indices, list) or not indices or any(type(i) is not int for i in indices)):
            raise MethodError("pac_grids must be 'all' or an explicit index list")
    return c

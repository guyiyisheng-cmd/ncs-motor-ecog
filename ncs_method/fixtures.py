"""Synthetic SOFTWARE-TEST fixtures. Never use these files as patient evidence."""
from __future__ import annotations
from pathlib import Path
import numpy as np
from .io import write_json


def make_fixture(directory: Path, n_resamples=40, n_subjects=2) -> Path:
    directory.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(83413)
    config = {"schema": "ncs-run-1", "method_reference": "docs/METHOD_CN.md#explicit-estimands",
              "conditions": ["Move", "Imagine"], "task": [0.0, 5.0], "baseline": [-2.0, 0.0],
              "include_right_endpoint": True, "n_resamples": n_resamples, "seed": 20260927,
              "pac_quantile": 0.95, "pac_grids": {"full": "all", "narrow": [0, 1]},
              "min_valid_fraction": 0.95, "subjects": [], "structure": [], "spatial_pairs": None}
    for i in range(n_subjects):
        subject, record = f"TEST{i+1:02d}", f"TESTREC{i+1:02d}"
        rounds = [f"R{k+1:02d}" for k in range(3)]
        actions = ["left_finger", "right_finger", "left_fist", "right_fist", "lip"]
        channels = [f"C{k+1:02d}" for k in range(6)]
        events = [{"event_id": f"E{len(actions)*2*r+2*a+c:03d}", "round_id": rd, "action": ac, "condition": co}
                  for r, rd in enumerate(rounds) for a, ac in enumerate(actions) for c, co in enumerate(config["conditions"])]
        e, c, t = len(events), len(channels), np.linspace(-2, 5, 29)
        beta = -2 + rng.normal(size=(e, c, len(t))) * 0.4
        task_mask = t >= 0
        for j, event in enumerate(events):
            beta[j, :, task_mask] += (-0.3 if event["condition"] == "Move" else 0.2)
        task = rng.uniform(0.0001, 0.005, size=(e, c, 6, 3, 3))
        base = rng.uniform(0.0001, 0.003, size=(e, c, 1, 3, 3))
        np.savez_compressed(directory / f"{subject}.npz", beta_db=beta, times_s=t, pac_task_mi=task,
                            pac_baseline_mi=base, amplitude_power_db=rng.normal(size=(e, c)),
                            event_ids=np.array([x["event_id"] for x in events]), channel_ids=np.array(channels))
        metadata = {"schema": "ncs-arrays-1", "dataset_kind": "synthetic_software_test", "subject": subject, "record": record,
                    "event_channel_alignment_reviewed": True, "source_array_provenance_reviewed": True,
                    "mi_normalization": "per_window_per_phase_bin_means", "beta_unit": "dB", "mi_unit": "dimensionless",
                    "task_windows": 6, "baseline_windows": 1, "actions": actions, "channels": channels, "rounds": rounds,
                    "conditions": config["conditions"], "events": events,
                    "phase_bands_hz": [[13, 17], [15, 19], [17, 21]],
                    "amplitude_bands_hz": [[70, 80], [80, 90], [90, 98]],
                    "amplitude_power_unit": "dB", "amplitude_power_aggregation": "event_scalar_median_within_action_condition"}
        write_json(directory / f"{subject}.json", metadata)
        config["subjects"].append({"metadata": f"{subject}.json", "arrays": f"{subject}.npz"})
    affine = np.diag([2., 2., 2., 1.])
    fa = np.ones((4, 4, 4)) * 0.5
    left = np.zeros_like(fa); right = np.zeros_like(fa)
    left[0:2, 1:3, 1:3] = 1; right[2:4, 1:3, 1:3] = 1
    np.savez_compressed(directory / "TEST_CST.npz", fa=fa, md=fa * 0.002, mask_left=left, mask_right=right,
                        fa_affine=affine, md_affine=affine, left_affine=affine, right_affine=affine, spatial_unit=np.array("mm"))
    config["structure"] = [{"subject": "TEST01", "arrays": "TEST_CST.npz", "native_geometry_reviewed": True,
                             "dataset_kind": "synthetic_software_test"}]
    write_json(directory / "config.json", config)
    return directory / "config.json"

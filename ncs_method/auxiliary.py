"""Optional native-grid structure and explicitly evidenced spatial pairs.

This module does NOT register brains or invent missing contact coordinates.
Data availability is an explicit state, not a zero correlation.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import csv
import numpy as np
from .core import MethodError, finite_array, association
from .data import resolve_input, token


def quantify_native_cst(path: Path, subject: str) -> list[dict]:
    """Canonical NPZ with a separate source affine for EACH image/mask.

    Required: fa, mask_left, mask_right, fa_affine, left_affine, right_affine,
    spatial_unit ('mm'); optional md/rd/ad and their own *_affine.
    Numeric affinity is necessary, never sufficient for anatomical registration.
    """
    with np.load(path, allow_pickle=False) as z:
        fa = np.asarray(z["fa"], float)
        aff = finite_array(z["fa_affine"], "fa_affine")
        if fa.ndim != 3 or aff.shape != (4, 4) or str(z["spatial_unit"].item()) != "mm":
            raise MethodError("structure requires 3D FA, 4x4 source affine and explicit millimetres")
        if not np.allclose(aff[3], [0, 0, 0, 1], rtol=0, atol=1e-12):
            raise MethodError("invalid affine bottom row")
        voxel_volume = float(abs(np.linalg.det(aff[:3, :3])))
        if voxel_volume <= 0:
            raise MethodError("singular FA affine")
        masks = {}
        for side in ("left", "right"):
            raw = finite_array(z["mask_" + side], "mask_" + side)
            sa = finite_array(z[side + "_affine"], side + "_affine")
            if raw.shape != fa.shape or sa.shape != (4, 4) or not np.allclose(sa, aff, rtol=0, atol=0.001):
                raise MethodError("CST mask is not on the declared native FA grid")
            if not np.isin(raw, [0, 1]).all() or not np.any(raw):
                raise MethodError("CST masks must be nonempty binary arrays; no automatic threshold selection")
            masks[side] = raw.astype(bool)
        scalars = {"fa": fa}
        for name in ("md", "rd", "ad"):
            if name in z:
                a = np.asarray(z[name], float)
                sa = np.asarray(z[name + "_affine"], float)
                if a.shape != fa.shape or sa.shape != (4, 4) or not np.allclose(sa, aff, rtol=0, atol=0.001):
                    raise MethodError("scalar and FA grids differ")
                scalars[name] = a
        overlap = int(np.count_nonzero(masks["left"] & masks["right"]))
        rows = []
        for side, mask in masks.items():
            row = {"subject": token(subject, "subject"), "side": side,
                   "n_voxels": int(mask.sum()), "volume_mm3": float(mask.sum() * voxel_volume),
                   "overlap_voxels": overlap, "sampling": "uniform_finite_native_mask_voxels"}
            for name, a in scalars.items():
                values = a[mask]
                valid = values[np.isfinite(values)]
                row[name + "_mean"] = float(valid.mean()) if len(valid) else np.nan
                row[name + "_n_finite"] = len(valid)
            rows.append(row)
        return rows


def summarize_spatial(path: Path | None):
    if path is None:
        return [], {"status": "not_available", "n_complete_pairs": 0,
                    "reason": "No evidenced spatial-pair file supplied; no correlation was estimated."}
    required = ["subject", "record", "action", "contrast", "location_id", "space_id", "task_evidence_id",
                "location_evidence_id", "pairing_status", "image_effect", "beta_delta", "pac_delta"]
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not set(required).issubset(reader.fieldnames or []):
            raise MethodError("spatial CSV does not meet the declared data contract")
        raw_rows = list(reader)
    groups, seen = defaultdict(list), set()
    for row in raw_rows:
        # No silent selection of only favourable/complete rows from a candidate file.
        if row["pairing_status"] != "source_verified":
            raise MethodError("spatial file contains unverified candidates; use a separate candidate ledger")
        for k in required[:8]:
            token(row[k], "spatial " + k)
        key = tuple(row[k] for k in ("subject", "record", "action", "contrast", "location_id", "space_id"))
        if key in seen:
            raise MethodError("duplicate spatial key")
        seen.add(key)
        vector = np.array([float(row[k]) for k in ("image_effect", "beta_delta", "pac_delta")])
        if not np.isfinite(vector).all():
            raise MethodError("missing spatial number is not a zero effect")
        groups[key[:4] + (row["space_id"],)].append(vector)
    output = []
    for group, data in sorted(groups.items()):
        arr = np.asarray(data)
        image_beta = association(arr[:, 0], arr[:, 1])["rho"]
        image_pac = association(arr[:, 0], arr[:, 2])["rho"]
        output.append(dict(zip(["subject", "record", "action", "contrast", "space_id"], group)) |
                      {"n_locations": len(data), "rho_image_beta": image_beta, "rho_image_pac": image_pac,
                       "inference": "descriptive_only_no_spatial_independence_assumption",
                       "evidence_scope": "source_asserted_pairing_not_independently_validated_by_this_code"})
    return output, {"status": "descriptive_pairs_available" if len(seen) else "not_estimable",
                    "n_complete_pairs": len(seen), "n_groups": len(groups),
                    "note": "Two different rho values do not themselves test a difference between associations."}

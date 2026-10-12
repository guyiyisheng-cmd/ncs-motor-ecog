"""Portable, deterministic numeric outputs; public release is an explicit allowlist."""
from __future__ import annotations
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import sys
import platform
import zipfile
import numpy as np
from .core import MethodError


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(x) for x in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    return value


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(clean(value), f, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")


def write_csv(path: Path, rows: list[dict], fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(dict.fromkeys(k for r in rows for k in r))
    if not fieldnames:
        fieldnames = ["status"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            values = clean(row)
            writer.writerow({k: format(v, ".17g") if isinstance(v, float) else v for k, v in values.items()})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def environment() -> dict:
    return {"python": sys.version.split()[0], "numpy": np.__version__, "platform": platform.system(),
            "machine": platform.machine(), "byteorder": sys.byteorder,
            "thread_environment": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}}


def compare_runs(first: Path, second: Path, rtol=1e-10, atol=1e-12) -> dict:
    """Compare numeric tables, not ZIP metadata, timestamps or rendering bytes."""
    af = {p.relative_to(first).as_posix() for p in (first / "tables").glob("*.csv")}
    bf = {p.relative_to(second).as_posix() for p in (second / "tables").glob("*.csv")}
    errors, differences = [], []
    for directory in (first, second):
        status_path = directory / "RUN_STATUS.json"
        if not status_path.is_file() or json.loads(status_path.read_text(encoding="utf-8")).get("status") != "COMPLETED_DECLARED_NUMERICAL_SCOPE":
            errors.append("a run is incomplete or failed")
    try:
        ma = json.loads((first / "run_manifest.json").read_text(encoding="utf-8"))
        mb = json.loads((second / "run_manifest.json").read_text(encoding="utf-8"))
        for key in ("package_version", "dataset_kind", "inputs", "method_reference", "numerical_code"):
            if key not in ma or key not in mb or ma[key] != mb[key]:
                errors.append("manifest mismatch: " + key)
    except (OSError, ValueError):
        errors.append("run manifest unavailable or malformed")
    if af != bf or not af:
        errors.append("output CSV file sets differ or are empty")
    for rel in sorted(af & bf):
        def read(p):
            with p.open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                return reader.fieldnames, list(reader)
        ah, a = read(first / rel); bh, b = read(second / rel)
        if ah != bh or len(a) != len(b):
            errors.append(f"{rel}: columns or row count differ")
            continue
        max_error = 0.0
        for ra, rb in zip(a, b):
            for k in ah:
                x, y = ra[k], rb[k]
                if x == y:
                    continue
                try:
                    nx, ny = float(x), float(y)
                except (ValueError, TypeError):
                    errors.append(f"{rel}: key/text/missingness mismatch in {k}")
                    continue
                if not np.isfinite([nx, ny]).all() or not np.isclose(nx, ny, rtol=rtol, atol=atol):
                    errors.append(f"{rel}: numeric mismatch in {k}")
                max_error = max(max_error, abs(nx - ny))
        differences.append({"file": rel, "max_absolute_numeric_error": max_error})
    # Availability states matter even when the tables are empty.
    for name in ("spatial_status.json", "structure_status.json"):
        pa, pb = first / name, second / name
        if not (pa.is_file() and pb.is_file()) or pa.read_bytes() != pb.read_bytes():
            errors.append(name + ": availability differs")
    return {"passed": not errors, "rtol": rtol, "atol": atol, "table_comparisons": differences,
            "errors": list(dict.fromkeys(errors)), "scope": "numerical_reproducibility_not_scientific_validation"}


def export_code(root: Path, destination: Path):
    """Only individually listed code/docs/tests; never sweep the working tree."""
    root = root.resolve()
    filelist = root / "release_files.json"
    paths = json.loads(filelist.read_text(encoding="utf-8"))["files"]
    allowed = []
    for rel in paths:
        p = root / rel
        if Path(rel).is_absolute() or ".." in Path(rel).parts or p.is_symlink() or not p.is_file():
            raise MethodError("unsafe/missing release allowlist member")
        if root not in p.resolve().parents:
            raise MethodError("release file resolves outside code directory")
        if any(x in Path(rel).parts for x in ("local", "outputs", "data", ".git", "PRIVATE_LOCAL")):
            raise MethodError("private/output path cannot be a code release member")
        if p.suffix.lower() in (".npz", ".npy", ".edf", ".nii", ".dcm", ".csv", ".docx", ".pdf"):
            raise MethodError("code-only release excludes patient arrays/tables/manuscripts")
        allowed.append((rel, p))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as z:
        for rel, p in allowed:
            z.write(p, "NCS_Method_V1/" + rel)
        z.writestr("NCS_Method_V1/CODE_RELEASE_NOTICE.txt",
                   "CODE-ONLY export. No patient data is automatically included.\n"
                   "Review all allowed file contents and licenses before public upload.\n"
                   "Synthetic software tests do not constitute clinical-data reproduction.\n")
    return {"n_files": len(allowed), "sha256": sha256(destination), "patients_auto_exported": False}

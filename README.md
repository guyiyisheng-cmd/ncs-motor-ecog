# NCS motor ECoG

Frozen numerical method **v1.0.0** with portable analysis and display entry points.
Original software release: **v1.0.0-ebio.20261012** (immutable).
Packaging/documentation revision: **2026-10-12.2**; numerical method remains v1.0.0.
Repository: https://github.com/guyiyisheng-cmd/ncs-motor-ecog

This release contains MIT-licensed software, schemas and synthetic tests. It contains **no patient observations, clinical arrays, images, identity mappings or manuscript files**. It is an exploratory secondary-analysis tool, not a validated clinical system. No DOI is assigned.

## Publicly runnable scope

Use Python 3.11 or later in a new environment. The numerical core requires only NumPy; display dependencies are separate.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
python run_ncs.py self-test
python run_ncs.py demo --out local/synthetic_demo
```

The self-test includes the original 44 core tests plus eight input-isolation tests. The demo generates explicitly artificial arrays and compares two runs of seven numerical tables. These outputs are **not real-patient result reproduction**. Actual run outcomes belong in the release verification record, not an inferred pass from the presence of code.

## Controlled inputs

```sh
python reproduce.py --config /authorized/numeric/config.json --display-input /authorized/display --out local/new_run
python render_figures.py --input-dir /authorized/display --out local/figures
python export_tables.py --input-dir /authorized/display --table all --out local/tables
```

Replace `/authorized/...` with access-approved directories. No such directories are supplied or downloaded by these commands. The numerical entry starts with valid, explicitly keyed event arrays and saved complete-round indices, not raw EDF or BOLD. Display entry points use frozen CSV/NPZ/SVG inputs; each selected figure now loads only its declared dependencies; use `python render_figures.py --group 6 --list-inputs` to list them. The reference and figure source bundle are not public. The current manuscript's cohort-branch Figure 1 also requires its confirmed source SVG; no older illustration can substitute for it.

See [REPRODUCTION.md](REPRODUCTION.md), [INPUT_SCHEMA.md](INPUT_SCHEMA.md), [FIGURE_TABLE_REPRODUCTION_MAP.csv](FIGURE_TABLE_REPRODUCTION_MAP.csv), and [DATA_ACCESS.md](DATA_ACCESS.md). Full historical display dependencies are recorded in `ENVIRONMENT/requirements-tested.txt`; they are not required for synthetic core tests and the current verification record distinguishes the fresh array-display environment from untested SVG/system-Cairo dependencies.

## Scientific and rights boundaries

Four ECoG patients and three CST patients overlap in one patient. Channels, actions and windows are repeated observations, not independent patients. Array ordering is not an MRI coordinate. Spatial task-imaging–ECoG relationships remain unestimated. The original PAC aggregation order and complete-round resampling are retained. Computational reproduction establishes neither physiological independence nor PAC superiority.

The original numerical code and authorized later display/wrapper/documentation code are released under MIT. Dependencies retain their own upstream licenses and are not vendored. This software license grants no rights to patient data or third-party image assets. Permission for public release of patient-derived data has not yet been documented and verified for a defined set of files. No patient-derived data are included in this release. De-identification and willingness to share do not constitute a verified public-release permission.

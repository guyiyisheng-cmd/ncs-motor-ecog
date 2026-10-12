# Controlled input contracts

## Numerical starting point

`configs/config_template.json` is a schema template, not a clinical run. Relative array/metadata paths are resolved relative to the supplied config. For each subject: one stable-channel recording, explicit event IDs, round IDs, action and condition keys, channel IDs, reviewed upstream provenance. The program rejects misaligned keys, incomplete rounds and invalid grids; it does not infer identity from signal similarity.

`beta_db`: E×C×T; `times_s`: T. PAC can be E×C×W×A×P task and baseline MI arrays, or the declared `source_window_medians` interface with `pac_task_window_median` and `pac_baseline_window_median`: E×C×A×P. These are unsubtracted MI inputs in [0,1]. Preserve original window-median → task-minus-baseline → event-median → frequency-percentile order. Never substitute a single-event percentile table. `bootstrap_indices`: B×R integers in declared round order. Optional amplitude power is E×C with its original aggregation definition. All values, units and frequency grids must agree with reviewed metadata.

Structural NPZ inputs contain FA, binary left/right masks and **independent source affines** (`fa_affine`, `left_affine`, `right_affine`), spatial unit mm; optional MD/RD/AD and independent affines use mm²/s. Grid equality is not proof of anatomical registration. Leave `spatial_pairs` null when independent location/contrast evidence is absent. Full field descriptions are retained in `docs/INPUT_CONTRACT_CN.md` and validation code `ncs_method/data.py`.

## Display starting point

The display directory contains `SOURCE_DATA/`, `IMAGING/`, `ASSETS/`, `RUN_RECORDS/rendering.json` and `TABLES_EN.json`. `DISPLAY_INPUT_MANIFEST.csv` lists required file names, array keys/shapes or table columns, without patient values or paths. Assets are controlled and intentionally not bundled.

The renderer reads only selected-output dependencies declared in display/input_contract.py. Run `python render_figures.py --group 6 --list-inputs` for a precise list. Missing necessary files stop execution with their names; unrelated clinical files are not opened. Recorded channels are validated against the confirmed topology and saved array axes. A single formatted table can be supplied as Table_ID_EN.json without any other table.

`TABLES_EN.json` maps logical keys `1`, `S1`…`S9` to lists of `{caption, rows}` blocks. The export preserves all supplied rows verbatim, including continuation tables; it does not infer numbers from images. The clinical publication binder rebuilds S2–S5 and plotted core summaries from numerical outputs; other frozen descriptive/validation tables are carried from their approved source tables, not estimated anew.

All controlled directories stay outside this repository and are supplied via command-line paths. Clinical sharing requires explicit authorization; deidentified IDs do not alone authorize release.

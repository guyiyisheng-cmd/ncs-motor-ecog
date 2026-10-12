# Reproduction scope and commands

## Level 1: public software tests and synthetic computation

In a fresh directory extracted from this GitHub release, create a new Python 3.11+ virtual environment and install `requirements.txt` from public PyPI with `--no-cache-dir`. Do not set PYTHONPATH to the clinical workspace.

```sh
python run_ncs.py self-test
python run_ncs.py demo --out local/synthetic_demo
```

The demo executes two runs from artificial input arrays and writes `REPRODUCIBILITY_TEST.json`, including numerical-table comparisons. Synthetic agreement is not a validation of real-patient results. Release verification is recorded separately with the downloaded commit and archive hash. No patient result table or figure is publicly reproducible without additional authorized inputs in this code-only release.

## Level 2: numerical recomputation from controlled valid event arrays

```sh
python run_ncs.py run --config /authorized/numeric/config.json --out local/numeric
python compare_relocated.py /authorized/reference_run local/numeric --out local/relocation_check.json
```

The frozen v1.0 core starts with explicitly keyed events/actions/channels and saved complete-round indices. It does not reconstruct raw EDF/BOLD preprocessing. The private frozen reference is not shipped. The comparator normalizes only input path spellings and checks the remaining configuration, input hashes and numerical core. Numerical tolerances are rtol=1e-10 and atol=1e-12. Paths that change on relocation are not evidence of byte-identical configuration files.

## Level 3: controlled-input display and table export

```sh
python reproduce.py --config /authorized/numeric/config.json --display-input /authorized/display --out local/end_to_end
python render_figures.py --input-dir /authorized/display --out local/figures
python export_tables.py --input-dir /authorized/display --table all --out local/tables
```

The map in `FIGURE_TABLE_REPRODUCTION_MAP.csv` enumerates 37 output records: seven main figures, 19 supplementary figure files, ten logical tables and one movie. Each names its input contract and executable entry. Some logical supplementary figures span several files. Each figure now reads only the paths listed by `python render_figures.py --group <ID> --list-inputs`. Missing necessary inputs are reported explicitly; unrelated images, source SVGs, static arrays or time courses are not required. The full DISPLAY_INPUT_MANIFEST.csv remains a historical bundle inventory, not a single-figure requirement. Individual IDs include 1–7, S1–S8, S9a–e, S10a–e, S11 and movie. A single table accepts `Table_S1_EN.json` (substitute the selected ID); it does not open TABLES_EN.json if the single-table file exists. Legacy complete bundles remain supported. Table export copies supplied cells; it is not a new estimate from source observations. See MINIMAL_INPUTS.md.

TFR, time-course and array caches, FA/mask inputs, selected slices, approved source illustrations and the English table bundle remain controlled. Renderers do not create missing observations, new coordinates, registrations, dynamic PAC or interpolated physiological frames. Movie output is the existing five-window beta GIF; MP4 encoding is a separate format step. The current cohort-branch Figure 1 needs its current approved SVG; the older source-asset contract alone cannot reproduce this revised illustration. The software does not generate Word manuscripts.

## Historical local verification versus this release

The earlier local candidate was tested with authorized clinical inputs: seven numerical tables agreed with frozen references within 4.44e-16 maximum absolute error. That historical local check is not an anonymous remote-download patient-data reproduction. Clinical source inputs and private comparison logs are excluded here. Only operations actually executed on downloaded public code may be reported as verification of that commit. Current local controlled-input redraw checks are distinct from an external recipient receiving approved inputs and reproducing them. The latter has not occurred.

## Environment and access

`requirements.txt` pins the public core dependency. `ENVIRONMENT/requirements-tested.txt` and `ENVIRONMENT/tested_platform.json` record the earlier complete display environment; not every package in that historical environment has been verified on a fresh public install. CairoSVG additionally requires system Cairo. No second-OS or cloud-CI result is claimed. `ENVIRONMENT/requirements-array.txt` pins the four main array-display dependencies. SVG figures additionally need CairoSVG/system Cairo; they are not silently required for array-only rendering. Fonts/caches must be created in the new environment. Pixel-byte equality across platforms is not promised; numerical values, point positions, limits and aggregation order must remain fixed.

See `DATA_ACCESS.md` for the restricted-data boundary. There is currently no public download of the clinical input bundle and no released clinical expected-output table.

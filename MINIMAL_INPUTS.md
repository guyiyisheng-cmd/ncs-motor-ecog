# Minimal input contracts

These are file dependencies, not data-release permissions. No real inputs are shipped. Preserve the subdirectories shown below. No values are imputed and no synthetic fallback exists.

|Output|Required files|
|---|---|
|1|`ASSETS/Figure1_visual_refinement.svg`|
|2|`SOURCE_DATA/IMAGING_CST_quantitative_reused.csv`; `SOURCE_DATA/IMAGING_HUBO-P01_deidentified_selected_slices.npz`; `IMAGING/HUBO-P01_structure.npz`; `SOURCE_DATA/IMAGING_HUBO-P06_deidentified_selected_slices.npz`; `IMAGING/HUBO-P06_structure.npz`; `SOURCE_DATA/IMAGING_HUBO-P07_deidentified_selected_slices.npz`; `IMAGING/HUBO-P07_structure.npz`|
|3|`SOURCE_DATA/TASK_P08_C1_tfr.npz`; `SOURCE_DATA/TEMPORAL_all_channel_beta_summary.csv.gz`|
|4|`SOURCE_DATA/JOINT_patient_action_estimates.csv`; `SOURCE_DATA/JOINT_channel_pairs.csv`|
|5|`SOURCE_DATA/JOINT_channel_pairs.csv`; `SOURCE_DATA/JOINT_patient_associations.csv`|
|6|`SOURCE_DATA/P07_static_arrays.csv`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|
|7|`SOURCE_DATA/P07_pooled_dynamic_windows.csv`; `SOURCE_DATA/P07_pooled_beta_curves.npz`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|
|S1|`SOURCE_DATA/TASK_all_channel_pooled_beta.csv`|
|S2|`SOURCE_DATA/TASK_P08_C1_corrected_PAC_grid.csv`|
|S3|`SOURCE_DATA/TASK_HUBO-P07_C2_tfr.npz`; `SOURCE_DATA/TASK_HUBO-P04_C1_tfr.npz`; `SOURCE_DATA/TASK_HUBO-P10_C1_tfr.npz`|
|S4|`ASSETS/Figure_S4_registration.svg`|
|S5|`SOURCE_DATA/BASELINE_pooled_channels.csv`; `SOURCE_DATA/BASELINE_patient_action.csv`; `SOURCE_DATA/BASELINE_patient_rho.csv`|
|S6|`ASSETS/Figure_S6_surface_overview_detail.svg`|
|S7|`SOURCE_DATA/P07_allchannel_TFR_display.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|S8|`SOURCE_DATA/P07_allchannel_TFR_display.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|S9a|`SOURCE_DATA/P07_beta_display_curves.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|S9b|`SOURCE_DATA/P07_beta_display_curves.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|S9c|`SOURCE_DATA/P07_beta_display_curves.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|S9d|`SOURCE_DATA/P07_beta_display_curves.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|S9e|`SOURCE_DATA/P07_beta_display_curves.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|S10a|`SOURCE_DATA/P07_beta_dynamic_windows.csv`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|
|S10b|`SOURCE_DATA/P07_beta_dynamic_windows.csv`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|
|S10c|`SOURCE_DATA/P07_beta_dynamic_windows.csv`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|
|S10d|`SOURCE_DATA/P07_beta_dynamic_windows.csv`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|
|S10e|`SOURCE_DATA/P07_beta_dynamic_windows.csv`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|
|S11|`SOURCE_DATA/P07_pooled_beta_curves.npz`; `SOURCE_DATA/P07_contact_topology.csv`|
|movie|`SOURCE_DATA/P07_beta_dynamic_windows.csv`; `SOURCE_DATA/P07_contact_topology.csv`; `RUN_RECORDS/rendering.json`|

For a single logical table, provide only `Table_<ID>_EN.json`. This exports the exact supplied rows and does not recompute estimates or uncertainty. The legacy TABLES_EN.json remains optional when the single-table JSON is supplied.

The eight numerical CSV candidates for Tables S1–S6 and S8 are unrounded source observations/summaries, not interchangeable with the formatted table JSON. Reconstructing presentation cells requires the manuscript-specific column/rounding map. Uncertainty cannot be regenerated from published ranges or correlations alone.

Topology is read independently from `P07_contact_topology.csv`; the saved channel axis is checked against it. The frozen three-strip/contact order and missing contacts must match. The loader does not infer MRI coordinates from topology columns. Fixed limits come from rendering.json only for displays that use them. Full time courses carry their own time and channel axes.

Example: `python render_figures.py --group 6 --input-dir /approved/minimal6 --out local/figure6`. Only its three listed inputs are required. `--list-inputs` requires no plotting library or clinical input.

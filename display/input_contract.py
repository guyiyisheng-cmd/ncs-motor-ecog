"""Per-output display dependencies. No clinical values or numerical estimators."""
from pathlib import Path

S = 'SOURCE_DATA/'
TOPOLOGY = S + 'P07_contact_topology.csv'
LIMITS = 'RUN_RECORDS/rendering.json'
INPUTS = {
    '1': ['ASSETS/Figure1_visual_refinement.svg'],
    '2': [S+'IMAGING_CST_quantitative_reused.csv'] + [p for pid in ('P01','P06','P07') for p in (S+f'IMAGING_HUBO-{pid}_deidentified_selected_slices.npz', f'IMAGING/HUBO-{pid}_structure.npz')],
    '3': [S+'TASK_P08_C1_tfr.npz', S+'TEMPORAL_all_channel_beta_summary.csv.gz'],
    '4': [S+'JOINT_patient_action_estimates.csv', S+'JOINT_channel_pairs.csv'],
    '5': [S+'JOINT_channel_pairs.csv', S+'JOINT_patient_associations.csv'],
    '6': [S+'P07_static_arrays.csv', TOPOLOGY, LIMITS],
    '7': [S+'P07_pooled_dynamic_windows.csv', S+'P07_pooled_beta_curves.npz', TOPOLOGY, LIMITS],
    'S1': [S+'TASK_all_channel_pooled_beta.csv'],
    'S2': [S+'TASK_P08_C1_corrected_PAC_grid.csv'],
    'S3': [S+f'TASK_HUBO-{pid}_{ch}_tfr.npz' for pid,ch in (('P07','C2'),('P04','C1'),('P10','C1'))],
    'S4': ['ASSETS/Figure_S4_registration.svg'],
    'S5': [S+'BASELINE_pooled_channels.csv', S+'BASELINE_patient_action.csv', S+'BASELINE_patient_rho.csv'],
    'S6': ['ASSETS/Figure_S6_surface_overview_detail.svg'],
    'S7': [S+'P07_allchannel_TFR_display.npz', TOPOLOGY],
    'S8': [S+'P07_allchannel_TFR_display.npz', TOPOLOGY],
    **{f'S9{letter}': [S+'P07_beta_display_curves.npz', TOPOLOGY] for letter in 'abcde'},
    **{f'S10{letter}': [S+'P07_beta_dynamic_windows.csv', TOPOLOGY, LIMITS] for letter in 'abcde'},
    'S11': [S+'P07_pooled_beta_curves.npz', TOPOLOGY],
    'movie': [S+'P07_beta_dynamic_windows.csv', TOPOLOGY, LIMITS],
}
GROUPS = {key: [key] for key in INPUTS}
GROUPS.update({'3-5,S1-S6': ['3','4','5']+[f'S{i}' for i in range(1,7)],
               'S7-S11': ['S7','S8']+[f'S9{x}' for x in 'abcde']+[f'S10{x}' for x in 'abcde']+['S11'],
               'S9': [f'S9{x}' for x in 'abcde'], 'S10': [f'S10{x}' for x in 'abcde'],
               'all': list(INPUTS)})

def required_inputs(group):
    return sorted({p for item in GROUPS[group] for p in INPUTS[item]})

def check_inputs(root, group):
    missing = [p for p in required_inputs(group) if not (Path(root)/p).is_file()]
    if missing:
        raise FileNotFoundError('Missing required input(s) for '+group+':\n'+'\n'.join(missing))
    return required_inputs(group)

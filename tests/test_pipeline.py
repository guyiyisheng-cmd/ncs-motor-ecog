"""Temporary synthetic data only. No patient identifiers, arrays, or credentials."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from ncs_method.fixtures import make_fixture
from ncs_method.data import load_subject, read_json, validate_config
from ncs_method.analysis import estimate, indices_for, bootstrap_subject
from ncs_method.runner import run
from ncs_method.io import compare_runs, write_json, write_csv, export_code
from ncs_method.core import MethodError
from ncs_method.auxiliary import quantify_native_cst, summarize_spatial


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_path = make_fixture(self.root / 'input', 20, n_subjects=1)
        self.cfg = read_json(self.config_path)

    def tearDown(self):
        self.tmp.cleanup()

    def subject(self):
        return load_subject(self.cfg['subjects'][0], self.config_path.parent, self.cfg)

    def test_valid_contract(self):
        s = self.subject(); self.assertEqual(s.beta.shape, (30, 6, 29))
        self.assertEqual(len(s.rounds), 3)

    def test_duplicate_event_fails(self):
        p = self.config_path.parent / 'TEST01.json'; m = read_json(p)
        m['events'][1] = dict(m['events'][0]); write_json(p, m)
        with self.assertRaises(MethodError): self.subject()

    def test_missing_event_fails_not_zero_imputed(self):
        p = self.config_path.parent / 'TEST01.json'; m = read_json(p)
        m['events'].pop(); write_json(p, m)
        with self.assertRaises(MethodError): self.subject()

    def test_array_event_order_mismatch_fails(self):
        p = self.config_path.parent / 'TEST01.json'; m = read_json(p)
        m['events'][0], m['events'][1] = m['events'][1], m['events'][0]; write_json(p, m)
        with self.assertRaises(MethodError): self.subject()

    def test_window_metadata_mismatch_fails(self):
        p = self.config_path.parent / 'TEST01.json'; m = read_json(p); m['task_windows'] = 7; write_json(p, m)
        with self.assertRaises(MethodError): self.subject()

    def test_same_round_counts_apply_to_all_actions_conditions(self):
        s = self.subject()
        for a in s.actions:
            for c in s.conditions:
                ix = indices_for(s, a, c, [2, 0, 1])
                self.assertEqual(len(ix), 3)
                self.assertEqual(ix[0], ix[1])
                self.assertNotEqual(ix[0], ix[2])

    def test_channel_and_pair_row_counts(self):
        s = self.subject(); _, channels, pairs, combined = estimate(s, self.cfg, [1, 1, 1], True)
        self.assertEqual(len(channels), 6 * 5 * 2); self.assertEqual(len(pairs), 6 * 5); self.assertEqual(len(combined), 12)
        self.assertEqual(len({(x['action'], x['channel']) for x in pairs}), len(pairs))

    def test_bootstrap_is_deterministic(self):
        a = bootstrap_subject(self.subject(), self.cfg)
        b = bootstrap_subject(self.subject(), self.cfg)
        np.testing.assert_equal(a[4], b[4])
        np.testing.assert_allclose([r['estimate'] for r in a[0]], [r['estimate'] for r in b[0]], equal_nan=True)

    def test_target_result_not_config(self):
        self.cfg['target_rho'] = .8
        with self.assertRaises(MethodError): validate_config(self.cfg)

    def test_complete_rerun_numerical_reproducibility(self):
        run(self.config_path, self.root / 'run1'); run(self.config_path, self.root / 'run2')
        self.assertTrue(compare_runs(self.root / 'run1', self.root / 'run2')['passed'])
        status = read_json(self.root / 'run1/RUN_STATUS.json')
        self.assertEqual(status['dataset_kind'], 'synthetic_software_test')
        self.assertFalse(status['raw_signal_preprocessing_run_by_this_command'])

    def test_cannot_overwrite_existing_results(self):
        out = self.root / 'output'; out.mkdir()
        with self.assertRaises(MethodError): run(self.config_path, out)

    def test_spatial_missing_not_zero_rho(self):
        rows, status = summarize_spatial(None)
        self.assertEqual(rows, []); self.assertEqual(status['status'], 'not_available')
        self.assertNotIn('rho', status)

    def test_spatial_exact_pair_keys(self):
        p = self.root / 'spatial.csv'
        rows = [{'subject': 'TEST', 'record': 'REC', 'action': 'finger', 'contrast': 'imag_minus_move',
                 'location_id': f'L{k}', 'space_id': 'native', 'task_evidence_id': 'TE1', 'location_evidence_id': 'LE1',
                 'pairing_status': 'source_verified', 'image_effect': k, 'beta_delta': k * 2, 'pac_delta': -k} for k in range(5)]
        write_csv(p, rows)
        out, status = summarize_spatial(p)
        self.assertEqual(status['n_complete_pairs'], 5)
        self.assertAlmostEqual(out[0]['rho_image_beta'], 1)
        self.assertAlmostEqual(out[0]['rho_image_pac'], -1)
        rows.append(rows[0]); write_csv(p, rows)
        with self.assertRaises(MethodError): summarize_spatial(p)

    def test_unverified_spatial_candidates_rejected(self):
        p = self.root / 'spatial.csv'
        row = dict.fromkeys(['subject','record','action','contrast','location_id','space_id','task_evidence_id','location_evidence_id'], 'TEST')
        row.update(pairing_status='candidate', image_effect=1, beta_delta=2, pac_delta=3)
        write_csv(p, [row])
        with self.assertRaises(MethodError): summarize_spatial(p)

    def test_real_geometry_units_used_for_mask_volume(self):
        rows = quantify_native_cst(self.config_path.parent / 'TEST_CST.npz', 'TEST')
        self.assertEqual(rows[0]['n_voxels'], 8)
        self.assertAlmostEqual(rows[0]['volume_mm3'], 64.)
        self.assertEqual(rows[0]['overlap_voxels'], 0)

    def test_affine_mismatch_rejected(self):
        p = self.config_path.parent / 'TEST_CST.npz'
        with np.load(p, allow_pickle=False) as z: values = {k: z[k] for k in z.files}
        values['left_affine'] = values['left_affine'].copy(); values['left_affine'][0, 3] = 5.
        np.savez_compressed(p, **values)
        with self.assertRaises(MethodError): quantify_native_cst(p, 'TEST')

    def test_public_export_is_code_only(self):
        code = self.root / 'code'; code.mkdir(); (code / 'file.py').write_text('x=1\n')
        (code / 'private.csv').write_text('must_not_export\n')
        write_json(code / 'release_files.json', {'files': ['file.py']})
        info = export_code(code, self.root / 'release.zip')
        self.assertEqual(info['n_files'], 1); self.assertFalse(info['patients_auto_exported'])

    def test_private_csv_cannot_be_allowlisted(self):
        code = self.root / 'code'; code.mkdir(); (code / 'data.csv').write_text('private\n')
        write_json(code / 'release_files.json', {'files': ['data.csv']})
        with self.assertRaises(MethodError): export_code(code, self.root / 'bad.zip')

    def test_release_path_traversal_rejected(self):
        code = self.root / 'code'; code.mkdir(); (self.root / 'secret.py').write_text('secret\n')
        write_json(code / 'release_files.json', {'files': ['../secret.py']})
        with self.assertRaises(MethodError): export_code(code, self.root / 'bad.zip')

"""All cases in this file are mathematical/software fixtures, not human data."""
import unittest
import numpy as np
from ncs_method.core import (MethodError, mi_from_phase_amplitude, phase_bin_mi_reference,
    beta_from_events, pac_event_contrast, pac_from_events, average_ranks, pearson, association, conditional_range, time_mask)


class TestCore(unittest.TestCase):
    def setUp(self):
        self.phase = np.linspace(-np.pi, np.pi, 1800, endpoint=False) + 0.0003

    def test_mi_uniform_amplitude(self):
        self.assertAlmostEqual(float(mi_from_phase_amplitude(self.phase, np.ones(1800))), 0, places=12)

    def test_mi_reference_agreement(self):
        amp = 2 + 0.4 * np.cos(self.phase) + 0.2 * np.sin(2 * self.phase)
        self.assertAlmostEqual(float(mi_from_phase_amplitude(self.phase, amp)), phase_bin_mi_reference(self.phase, amp), places=12)

    def test_mi_positive_scale_invariance(self):
        amp = 1 + 0.7 * np.cos(self.phase)
        np.testing.assert_allclose(mi_from_phase_amplitude(self.phase, amp), mi_from_phase_amplitude(self.phase, amp * 1234), atol=1e-12)

    def test_mi_batch_invariance(self):
        phases = np.stack([self.phase] * 4).reshape(2, 2, -1)
        amps = 1 + np.arange(4).reshape(2, 2, 1) * 0.2 * np.cos(phases)
        batched = mi_from_phase_amplitude(phases, amps)
        reference = np.array([mi_from_phase_amplitude(p, a) for p, a in zip(phases.reshape(4, -1), amps.reshape(4, -1))]).reshape(2, 2)
        np.testing.assert_allclose(batched, reference, atol=1e-12)

    def test_mi_sample_permutation_invariance(self):
        amp = 1 + 0.7 * np.cos(self.phase)
        p = np.random.default_rng(3).permutation(len(amp))
        self.assertAlmostEqual(float(mi_from_phase_amplitude(self.phase, amp)), float(mi_from_phase_amplitude(self.phase[p], amp[p])), places=12)

    def test_mi_known_modulation_recovery(self):
        values = [float(mi_from_phase_amplitude(self.phase, 1 + m * np.cos(self.phase))) for m in (0, .2, .5, .8)]
        self.assertTrue(np.all(np.diff(values) > 0))

    def test_empty_phase_bin_rejected(self):
        with self.assertRaises(MethodError): mi_from_phase_amplitude(np.zeros(20), np.ones(20))

    def test_zero_amplitude_rejected(self):
        with self.assertRaises(MethodError): mi_from_phase_amplitude(self.phase, np.zeros(1800))

    def test_negative_amplitude_rejected(self):
        with self.assertRaises(MethodError): mi_from_phase_amplitude(self.phase, -np.ones(1800))

    def test_nonfinite_rejected(self):
        amp = np.ones(1800); amp[0] = np.nan
        with self.assertRaises(MethodError): mi_from_phase_amplitude(self.phase, amp)

    def test_beta_constant_offset_is_not_a_task_change(self):
        t = np.array([-2., -1., 0., 1., 2., 3., 4., 5.])
        beta = np.full((3, 2, 8), -3.)
        result = beta_from_events(beta, t, [0, 1, 2])
        np.testing.assert_allclose(result['original'], -3)
        np.testing.assert_allclose(result['same_scale'], 0)

    def test_beta_same_scale_offset_invariance(self):
        rng = np.random.default_rng(4); beta = rng.normal(size=(3, 2, 8)); t = np.arange(-2, 6.)
        a = beta_from_events(beta, t, [0, 1, 2]); b = beta_from_events(beta + 8, t, [0, 1, 2])
        np.testing.assert_allclose(a['same_scale'], b['same_scale'], atol=1e-12)
        np.testing.assert_allclose(a['original'] + 8, b['original'], atol=1e-12)

    def test_time_endpoint_explicit(self):
        t = np.array([-2., -1., 0., 1.])
        self.assertEqual(int(time_mask(t, (-2, 0), True).sum()), 3)
        self.assertEqual(int(time_mask(t, (-2, 0), False).sum()), 2)

    def test_pac_window_then_event_then_frequency_order(self):
        # Each event has a large value in a different cell; the cellwise median is zero.
        d = np.array([[.9, 0], [0, .9], [0, 0.]]).reshape(3, 1, 2, 1)
        correct = pac_from_events(d, [0, 1, 2], [0, 1])
        wrong_order = np.median(np.quantile(d.reshape(3, 2), .95, axis=1))
        self.assertEqual(float(correct[0]), 0)
        self.assertGreater(wrong_order, .8)

    def test_pac_window_counts_no_seventh_window(self):
        task = np.full((2, 1, 6, 2, 2), .2); base = np.full((2, 1, 1, 2, 2), .1)
        np.testing.assert_allclose(pac_event_contrast(task, base), .1)

    def test_pac_invalid_mi_rejected(self):
        with self.assertRaises(MethodError): pac_event_contrast(np.ones((2, 1, 6, 2, 2)) * 2, np.ones((2, 1, 1, 2, 2)))

    def test_midranks_ties(self):
        np.testing.assert_equal(average_ranks([3, 1, 1, 2]), [4, 1.5, 1.5, 3])

    def test_spearman_reverse(self):
        self.assertAlmostEqual(association([1, 2, 3, 4], [4, 3, 2, 1])['rho'], -1)

    def test_constant_rho_undefined(self):
        self.assertTrue(np.isnan(association([1, 1, 1], [1, 2, 3])['rho']))

    def test_partial_collinear_undefined(self):
        self.assertTrue(np.isnan(association([1, 2, 3, 4], [2, 4, 1, 3], [1, 2, 3, 4])['partial_rho']))

    def test_correlation_scaling_does_not_make_evidence(self):
        x, y = np.arange(5.), np.array([0, 3, 1, 4, 2.])
        self.assertAlmostEqual(association(x, y)['rho'], association(x * .001 + 5, y * .001)['rho'])

    def test_conditional_range_records_undefined_draws(self):
        ci = conditional_range([1.] * 98 + [np.nan] * 2)
        self.assertEqual(ci['n_valid'], 98); self.assertEqual(ci['lower'], 1.)
        self.assertTrue(np.isnan(conditional_range([1.] * 90 + [np.nan] * 10)['lower']))

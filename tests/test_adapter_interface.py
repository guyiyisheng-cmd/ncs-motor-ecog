"""Synthetic software tests, no clinical data."""
import unittest,tempfile,json
from pathlib import Path
import numpy as np
from ncs_method.core import pac_event_contrast,pac_window_median_contrast,MethodError
from ncs_method.fixtures import make_fixture
from ncs_method.data import load_subject,read_json
from adapters.project_adapter import keyed_reorder

class TestMedianInterface(unittest.TestCase):
 def test_window_and_median_interfaces_equivalent(self):
  with tempfile.TemporaryDirectory() as d:
   cfgpath=make_fixture(Path(d)/'synthetic_software_test',n_resamples=20);cfg=read_json(cfgpath);item=cfg['subjects'][0]
   a=load_subject(item,cfgpath.parent,cfg)
   ap=cfgpath.parent/item['arrays'];mp=cfgpath.parent/item['metadata'];m=read_json(mp)
   with np.load(ap) as z:arrays={k:z[k] for k in z.files}
   arrays['pac_task_window_median']=np.median(arrays.pop('pac_task_mi'),axis=2);arrays['pac_baseline_window_median']=np.median(arrays.pop('pac_baseline_mi'),axis=2)
   m.update(pac_input_form='source_window_medians',source_window_aggregation='median_over_windows_before_event_aggregation')
   np.savez_compressed(ap,**arrays);mp.write_text(json.dumps(m));b=load_subject(item,cfgpath.parent,cfg)
   np.testing.assert_array_equal(a.pac_delta,b.pac_delta)
   from ncs_method.analysis import estimate
   old=estimate(a,cfg,np.ones(len(a.rounds),int))[0];new=estimate(b,cfg,np.ones(len(b.rounds),int))[0]
   np.testing.assert_allclose(list(old.values()),list(new.values()),rtol=0,atol=0,equal_nan=True)
 def test_subtracted_or_invalid_grids_rejected(self):
  with self.assertRaises(MethodError):pac_window_median_contrast(np.full((2,3,4,5),-.1),np.zeros((2,3,4,5)))
  with self.assertRaises(MethodError):pac_window_median_contrast(np.ones((2,3,4,5)),np.ones((2,3,5,4)))
 def test_explicit_key_reorder(self):
  self.assertEqual(keyed_reorder(['b','a'],['a','b'],'test'),[1,0])
  for a,b in [(['a','a'],['a','b']),(['a','c'],['a','b'])]:
   with self.assertRaises(MethodError):keyed_reorder(a,b,'test')

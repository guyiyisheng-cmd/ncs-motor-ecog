"""Software packaging tests only; no patient observations are provided."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
contract=module('contract',ROOT/'display/input_contract.py')
tables=module('tables',ROOT/'export_tables.py')

class MinimalInputs(unittest.TestCase):
 def test_static_needs_no_curves_or_imaging(self):
  self.assertEqual(set(contract.required_inputs('6')),{'SOURCE_DATA/P07_static_arrays.csv',contract.TOPOLOGY,contract.LIMITS})
 def test_one_action_curve_needs_no_static_windows_or_imaging(self):
  self.assertEqual(set(contract.required_inputs('S9a')),{'SOURCE_DATA/P07_beta_display_curves.npz',contract.TOPOLOGY})
 def test_pooled_curve_needs_no_rendering_limits(self):
  self.assertEqual(set(contract.required_inputs('S11')),{'SOURCE_DATA/P07_pooled_beta_curves.npz',contract.TOPOLOGY})
 def test_subset_present_is_sufficient(self):
  with tempfile.TemporaryDirectory() as d:
   for p in contract.required_inputs('7'):
    f=Path(d)/p;f.parent.mkdir(parents=True,exist_ok=True);f.touch()
   self.assertEqual(contract.check_inputs(d,'7'),contract.required_inputs('7'))
 def test_missing_input_report_is_specific(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError) as caught:contract.check_inputs(d,'S11')
   self.assertIn('P07_pooled_beta_curves.npz',str(caught.exception));self.assertNotIn('IMAGING',str(caught.exception))
 def test_single_table_does_not_read_invalid_legacy_bundle(self):
  with tempfile.TemporaryDirectory() as d:
   expected=[{'rows':[['synthetic','value'],['example','1.25']]}]
   (Path(d)/'Table_S1_EN.json').write_text(json.dumps(expected));(Path(d)/'TABLES_EN.json').write_text('invalid and must never be opened')
   self.assertEqual(tables.load_table(d,'S1'),expected)
 def test_missing_table_never_becomes_synthetic(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError):tables.load_table(d,'S1')
 def test_all_is_exact_union(self):
  self.assertEqual(set(contract.required_inputs('all')),{p for paths in contract.INPUTS.values() for p in paths})
if __name__=='__main__':unittest.main()

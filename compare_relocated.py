"""Numerical comparison allowing only path relocation/JSON serialization changes.

The strict original comparator is preserved and recorded separately.
"""
from pathlib import Path
import argparse,json
from ncs_method.io import compare_runs
def canonical(config):
 c=json.loads(json.dumps(config))
 for item in c['subjects']:
  for key in ['arrays','metadata']:item[key]=Path(item[key]).name
 for item in c.get('structure',[]):item['arrays']=Path(item['arrays']).name
 return c
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 strict=compare_runs(a.reference,a.candidate)
 manifests=[json.loads((d/'run_manifest.json').read_text()) for d in [a.reference,a.candidate]]
 configs=[json.loads((d/'PRIVATE_LOCAL/executed_config.json').read_text()) for d in [a.reference,a.candidate]]
 same_config=canonical(configs[0])==canonical(configs[1])
 same_inputs=manifests[0]['inputs'][1:]==manifests[1]['inputs'][1:]
 same_core=manifests[0]['numerical_code']==manifests[1]['numerical_code']
 permitted_errors=all(e=='manifest mismatch: inputs' for e in strict['errors'])
 passed=same_config and same_inputs and same_core and permitted_errors
 report={'passed':passed,'scope':'numerical reproducibility after verified input-path relocation; not clinical validation','strict_comparison':strict,'nonconfig_input_digests_equal':same_inputs,'configuration_equal_after_path_canonicalization':same_config,'frozen_core_equal':same_core,'allowed_difference':'config file digest only, with unchanged canonical content'}
 a.out.write_text(json.dumps(report,indent=2));print('Relocated numerical comparison:', 'PASS' if passed else 'FAIL')
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()

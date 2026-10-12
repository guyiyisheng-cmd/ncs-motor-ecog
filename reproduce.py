"""Portable wrapper around unchanged NCS v1.0, starting from authorized arrays.

No EDF/BOLD preprocessing is implied. No data are downloaded or uploaded.
"""
from pathlib import Path
import argparse,subprocess,sys,shutil,json
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--config',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--display-input',type=Path)
 a=p.parse_args();root=Path(__file__).parent.resolve()
 if a.out.exists():p.error('Output must be new; original files are preserved.')
 a.out.mkdir(parents=True)
 subprocess.run([sys.executable,str(root/'run_ncs.py'),'run','--config',str(a.config.resolve()),'--out',str(a.out/'numeric')],check=True)
 if a.display_input:
  sys.path.insert(0,str(root/'display'));from bind_results import bind
  bundle=a.out/'display_input';shutil.copytree(a.display_input,bundle)
  (bundle/'RUN_RECORDS').mkdir(exist_ok=True)
  bind(bundle,a.out/'numeric',bundle)
  subprocess.run([sys.executable,str(root/'render_figures.py'),'--input-dir',str(bundle),'--out',str(a.out/'figures')],check=True)
 (a.out/'SCOPE.json').write_text(json.dumps({'start':'authorized valid event arrays','raw_EDF_BOLD_pipeline':False,'frozen_numerical_version':'1.0.0','display_arrays':'provided source caches for time-frequency/array extensions; not re-estimated by the numerical core','publication':'local only'},indent=2))
if __name__=='__main__':main()

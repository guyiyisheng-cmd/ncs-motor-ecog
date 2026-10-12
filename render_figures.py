"""Redraw selected frozen observations using only their required display inputs."""
from pathlib import Path
import argparse,os,sys,json,hashlib
sys.path.insert(0,str(Path(__file__).parent/'display'))
from input_contract import GROUPS,check_inputs,required_inputs

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-dir',type=Path)
 p.add_argument('--out',type=Path)
 p.add_argument('--group',choices=list(GROUPS),default='all')
 p.add_argument('--list-inputs',action='store_true',help='Print exact relative dependencies without loading clinical files or plotting libraries')
 a=p.parse_args()
 if a.list_inputs:
  print('\n'.join(required_inputs(a.group)));return
 if a.input_dir is None or a.out is None:p.error('--input-dir and --out are required for rendering')
 inp=a.input_dir.resolve(strict=True);out=a.out.resolve()
 try:files=check_inputs(inp,a.group)
 except FileNotFoundError as e:p.error(str(e))
 for f in ['FIGURES_MAIN_EN','FIGURES_SUPPLEMENTARY_EN','ANIMATION/FRAMES','QA','RUN_RECORDS','CODE']:(out/f).mkdir(parents=True,exist_ok=True)
 os.environ['NCS_DISPLAY_OUT']=str(out);os.environ['NCS_DISPLAY_INPUT']=str(inp)
 os.environ['MPLCONFIGDIR']=str(out/'QA/mpl_cache')
 import matplotlib
 fontdir=Path(matplotlib.get_data_path())/'fonts/ttf'
 (out/'QA/font_cache').mkdir(exist_ok=True)
 (out/'QA/fonts.conf').write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>{fontdir}</dir><cachedir>{out / "QA/font_cache"}</cachedir></fontconfig>')
 os.environ['FONTCONFIG_FILE']=str(out/'QA/fonts.conf')
 import render_core as m
 for item in GROUPS[a.group]:
  if item in ['1','2','6','7']:getattr(m,'f'+item)()
  elif item=='movie':m.animation()
  elif item in ['3','4','5'] or item in [f'S{i}' for i in range(1,7)]:m.old_plot_suite([item])
  else:m.si_grids([item])
  print(item,'complete',flush=True)
 import subprocess
 for item,stem in [('1','Figure_1_design'),('S4','Figure_S4_registration'),('S6','Figure_S6_surface_overview_detail')]:
  if item in GROUPS[a.group]:subprocess.run([sys.executable,str(Path(__file__).parent/'display/normalize_svg_pdf.py'),stem],check=True)
 if '1' in GROUPS[a.group]:subprocess.run([sys.executable,str(Path(__file__).parent/'display/encode_svg_text.py')],check=True)
 (out/'RUN_RECORDS/figure_manifest.json').write_text(json.dumps(m.manifest,ensure_ascii=False,indent=2))
 (out/'RUN_RECORDS/selected_inputs.json').write_text(json.dumps({'group':a.group,'files':[{ 'path':f,'sha256':hashlib.sha256((inp/f).read_bytes()).hexdigest()} for f in files],'research_estimator_called':False},indent=2))
 if 'movie' in GROUPS[a.group]:
  src=out/'ANIMATION/P07_beta_five_windows.gif';src.replace(out/'ANIMATION/Supplementary_Movie_1_EN.gif')
 print('English display export complete; no research estimator was called.')
if __name__=='__main__':main()

"""Redraw frozen observations in English from an authorized display-input bundle."""
from pathlib import Path
import argparse,os,sys,importlib.util,json

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-dir',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--group',choices=['all','1','2','3-5,S1-S6','6','7','S7-S11','movie'],default='all')
 a=p.parse_args();out=a.out.resolve();inp=a.input_dir.resolve(strict=True)
 for f in ['FIGURES_MAIN_EN','FIGURES_SUPPLEMENTARY_EN','ANIMATION/FRAMES','QA','RUN_RECORDS','CODE']:(out/f).mkdir(parents=True,exist_ok=True)
 os.environ['NCS_DISPLAY_OUT']=str(out);os.environ['NCS_DISPLAY_INPUT']=str(inp)
 os.environ['MPLCONFIGDIR']=str(out/'QA/mpl_cache')
 import matplotlib
 fontdir=Path(matplotlib.get_data_path())/'fonts/ttf'
 (out/'QA/font_cache').mkdir(exist_ok=True)
 (out/'QA/fonts.conf').write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>{fontdir}</dir><cachedir>{out / "QA/font_cache"}</cachedir></fontconfig>')
 os.environ['FONTCONFIG_FILE']=str(out/'QA/fonts.conf')
 sys.path.insert(0,str(Path(__file__).parent/'display'))
 import render_core as m
 groups={'1':['f1'],'2':['f2'],'3-5,S1-S6':['old_plot_suite'],'6':['f6'],'7':['f7'],'S7-S11':['si_grids'],'movie':['animation']}
 names=sum(groups.values(),[]) if a.group=='all' else groups[a.group]
 for name in names:getattr(m,name)();print(name,'complete',flush=True)
 import subprocess
 for stem in (['Figure_1_design'] if 'f1' in names else [])+(['Figure_S4_registration','Figure_S6_surface_overview_detail'] if 'old_plot_suite' in names else []):
  subprocess.run([sys.executable,str(Path(__file__).parent/'display/normalize_svg_pdf.py'),stem],check=True)
 if 'f1' in names:subprocess.run([sys.executable,str(Path(__file__).parent/'display/encode_svg_text.py')],check=True)
 (out/'RUN_RECORDS/figure_manifest.json').write_text(json.dumps(m.manifest,ensure_ascii=False,indent=2))
 if 'animation' in names:
  src=out/'ANIMATION/P07_beta_five_windows.gif';src.replace(out/'ANIMATION/Supplementary_Movie_1_EN.gif')
 print('English display export complete; no research estimator was called.')
if __name__=='__main__':main()

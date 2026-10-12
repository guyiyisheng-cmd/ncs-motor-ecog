"""Frozen-results display only. No research pipeline, filtering or resampling."""
from pathlib import Path
import os,sys,json,hashlib,importlib.util,xml.etree.ElementTree as ET,copy,io,base64
O=Path(os.environ['NCS_DISPLAY_OUT']).resolve();R=Path(os.environ['NCS_DISPLAY_INPUT']).resolve();Q=O/'QA'
os.environ['MPLCONFIGDIR']=str(Q/'mpl_cache');os.environ['FONTCONFIG_FILE']=str(Q/'fonts.conf')
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import Normalize,ListedColormap,LinearSegmentedColormap
from matplotlib.patches import Rectangle,ConnectionPatch,Patch
from PIL import Image
import cairosvg
from english_labels import install,fit_labels,translate
install()
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42,'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white','axes.linewidth':.6,'axes.spines.top':False,'axes.spines.right':False})
from layout_check import require_matplotlib_panel_alignment
OLD=R;AROOT=R/'SOURCE_DATA';BROOT=AROOT
CM=LinearSegmentedColormap.from_list('blue_white_orange',['#21658C','#FFFFFF','#BE5A20']);BLUE='#267B9B';ORANGE='#C27636';GRAY='#526570';LC='#2A7894';RC='#C48243';LINK='#87747A'
ACTS=['fingerLeft','fingerRight','fistLeft','fistRight','lip'];CN=['左指','右指','左拳','右拳','唇部'];STATE=['Move','Imagine','difference'];SCN=['执行','想象','想象−执行']
LIM=json.loads((OLD/'RUN_RECORDS/rendering.json').read_text())
S=pd.read_csv(AROOT/'P07_static_arrays.csv',float_precision='round_trip');D=pd.read_csv(AROOT/'P07_beta_dynamic_windows.csv',float_precision='round_trip');P=pd.read_csv(AROOT/'P07_pooled_dynamic_windows.csv',float_precision='round_trip')
Z=np.load(AROOT/'P07_pooled_beta_curves.npz');CH=Z['channels'].tolist();T=Z['times_s'];C=Z['values_db'];AZ=np.load(AROOT/'P07_beta_display_curves.npz')
manifest=[]
def js(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def ax(f,x,y,w,h):return f.add_axes([x/(f.get_figwidth()*25.4),y/(f.get_figheight()*25.4),w/(f.get_figwidth()*25.4),h/(f.get_figheight()*25.4)])
def tx(f,x,y,t,**kw):return f.text(x/(f.get_figwidth()*25.4),y/(f.get_figheight()*25.4),t,**kw)
def export(f,name,main=True,axes=None,rows=None,cols=None,sources=None):
 fit_labels(f);f.canvas.draw(); aa=axes if axes is not None else f.axes
 require_matplotlib_panel_alignment(f,axes=aa,panel_ids=[str(i) for i in range(len(aa))],row_groups=rows or [],column_groups=cols or [],json_out=Q/(name+'_alignment.json'),strict=True)
 p=O/('FIGURES_MAIN_EN' if main else 'FIGURES_SUPPLEMENTARY_EN')/name
 for ext in ['pdf','svg']:f.savefig(p.with_suffix('.'+ext))
 f.savefig(p.with_suffix('.png'),dpi=450)
 manifest.append({'stem':name,'sources':sources or [],'size_mm':[v*25.4 for v in f.get_size_inches()],'display_only':True});plt.close(f)
def gridgroups(nr,nc):return ([{'panels':[str(i*nc+j) for j in range(nc)]} for i in range(nr)],[{'panels':[str(i*nc+j) for i in range(nr)]} for j in range(nc)])
def vals(df,metric,state):
 if state=='difference':
  p=df.pivot(index='channel',columns='condition',values=metric);return (p.Imagine-p.Move).to_dict()
 return df[df.condition==state].set_index('channel')[metric].to_dict()
def bar(f,x,y,w,lim,label):
 ca=ax(f,x,y,w,2.6);c=f.colorbar(plt.cm.ScalarMappable(norm=Normalize(-lim,lim),cmap=CM),cax=ca,orientation='horizontal');c.set_ticks([-lim,0,lim]);c.ax.tick_params(labelsize=8,pad=2,length=2);c.outline.set_linewidth(.5);tx(f,x+w+4,y,label,fontsize=8)
def array(a,v,lim,matrix=False,highlight=False,labels=False):
 for s in range(3):
  if not matrix:a.plot(range(1,9),[s]*8,lw=.5,color='#dae0e3',zorder=0)
  for k in range(1,9):
   ch=f'C{s*8+k}';x=9-k
   if matrix:
    a.add_patch(Rectangle((x-.475,s-.38),.95,.76,facecolor=CM(Normalize(-lim,lim)(v[ch])) if ch in CH else 'white',edgecolor='#56636c' if ch in CH else '#89959b',lw=.28 if ch in CH else .6))
   elif ch in CH:a.scatter(x,s,s=43,c=[v[ch]],cmap=CM,vmin=-lim,vmax=lim,edgecolors='#56636c',linewidths=.3,zorder=2)
   else:a.scatter(x,s,s=40,facecolors='white',edgecolors='#89959b',linewidths=.65,marker='s',zorder=2)
   if highlight and ch=='C2':
    a.add_patch(Rectangle((x-.48,s-.40),.96,.8,fill=False,edgecolor='#232b32',lw=1,zorder=3))
    if labels:a.text(x,-.75,'C2',ha='center',va='center',fontsize=8,color='#232b32')
 a.set(xlim=(.35,8.65),ylim=(2.5,-1 if labels else -.5));a.axis('off')

def translate_svg(root):
 ns='http://www.w3.org/2000/svg'
 for e in root.iter('{'+ns+'}text'):
  if e.text:e.text=translate(e.text)
  st=e.get('style','').replace('Arial Unicode MS','DejaVu Sans');e.set('style',st)
 for e in root.iter():
  if 'font-family' in e.attrib:e.set('font-family','DejaVu Sans, sans-serif')

def f1():
 ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
 p=R/'ASSETS/Figure1_visual_refinement.svg';root=ET.parse(p).getroot();root.set('width','180mm');root.set('height','152mm')
 for e in root.iter('{'+ns+'}g'):
  if 'font-family' in e.attrib:e.set('font-family','DejaVu Sans, sans-serif')
 # Physical-size label harmonization; preserve all author illustration/source pixels.
 for e in root.iter('{'+ns+'}text'):
  s=float(e.get('font-size','25'));e.set('font-size',str(max(s,27)))
  swaps={'临床采集、记录阵列与任务比较':'术前影像—术中任务—同通道比较','仅表示单次任务的分析时间':'单次任务时钟；与采集顺序分层','人物和设备为方法示意；结构与ECoG子集仅共享P07。来源脑表面尚未建立当前患者的空间配对。':'人物与设备为示意；两子集仅共享P07。脑表面尚未绑定患者空间。'}
  if e.text in swaps:e.text=swaps[e.text]
 translate_svg(root)
 for e in root.iter('{'+ns+'}text'):
  if e.text=='Execute the action':e.text='Execution'
  if e.text=='Imagine the same action':e.text='Imagery'
  if e.text and '↔' in e.text:e.text='Δβ and ΔPAC'
 # Compute clips from the final English text, not the shorter source labels.
 defs=ET.SubElement(root,'{'+ns+'}defs')
 for i,e in enumerate(root.iter('{'+ns+'}text')):
  fs=float(e.get('font-size'));xx=float(e.get('x'));yy=float(e.get('y'));ww=max(5,len(e.text or ''))*fs*1.4;anchor=e.get('text-anchor','start')
  left=xx-(ww if anchor=='end' else ww/2 if anchor=='middle' else fs*.2)
  clip=ET.SubElement(defs,'{'+ns+'}clipPath',id=f'labelclip{i}',clipPathUnits='userSpaceOnUse');ET.SubElement(clip,'{'+ns+'}rect',x=str(left),y=str(yy-fs*1.5),width=str(ww+fs*.4),height=str(fs*2))
  e.set('clip-path',f'url(#labelclip{i})')
 out=O/'FIGURES_MAIN_EN/Figure_1_design.svg';ET.ElementTree(root).write(out,encoding='utf-8',xml_declaration=True)
 cairosvg.svg2pdf(url=str(out),write_to=str(out.with_suffix('.pdf')));cairosvg.svg2png(url=str(out),write_to=str(out.with_suffix('.png')),output_width=3189,output_height=2693)
 js(Q/'Figure_1_alignment_exemption.json',{'reason':'heterogeneous schematic; source illustrations preserved; no comparable quantitative axes'})
 manifest.append({'stem':out.stem,'sources':[str(p.relative_to(R))],'size_mm':[180,152],'clinical_illustrations':'schematic','brain':'source raster, no patient-space binding'})
def pixels(a,fa,ex,left=None,right=None,limits=(0,.8)):
 a.imshow(fa.T,extent=ex,origin='lower',cmap='gray',vmin=limits[0],vmax=limits[1],interpolation='nearest',resample=False)
 if left is not None:
  z=left.astype(int)+2*right.astype(int);a.imshow(np.ma.masked_equal(z.T,0),extent=ex,origin='lower',cmap=ListedColormap([LC,RC,'#806590']),vmin=.5,vmax=3.5,interpolation='nearest',resample=False,alpha=.8)
 a.set_aspect('equal');a.axis('off')
def direction(a,view,barlength,small=False):
 fs=7 if small else 8
 for xy,t,ha,va in ([] if small else [((-.04,.5),'L','right','center'),((1.04,.5),'R','left','center'),((.5,1.035),'A' if view=='axial' else 'S','center','bottom'),((.5,-.035),'P' if view=='axial' else 'I','center','top')]):a.text(*xy,t,transform=a.transAxes,ha=ha,va=va,fontsize=fs,clip_on=False)
 length=barlength/(a.get_xlim()[1]-a.get_xlim()[0]);x2=.98;x1=x2-length
 a.plot([x1,x2],[-.12,-.12],transform=a.transAxes,color='#333333',lw=1.1,clip_on=False)
 a.text((x1+x2)/2,-.18,f'{barlength} mm',transform=a.transAxes,ha='center',va='top',fontsize=7,clip_on=False)
def f2():
 f=plt.figure(figsize=(180/25.4,220/25.4));axes=[];checks=[]
 q=pd.read_csv(AROOT/'IMAGING_CST_quantitative_reused.csv',float_precision='round_trip')
 f.legend(handles=[Patch(facecolor=LC,label='左侧CST'),Patch(facecolor=RC,label='右侧CST')],loc='upper right',bbox_to_anchor=(.99,1.0),ncol=2,frameon=False,fontsize=8)
 tx(f,3,216,'原生FA与双侧CST',fontsize=10,fontweight='bold')
 for pi,pid in enumerate(['P01','P06','P07']):
  x=6+pi*60;tx(f,x,211,pid,fontsize=10,fontweight='bold')
  a=np.load(AROOT/f'IMAGING_HUBO-{pid}_deidentified_selected_slices.npz')
  z=np.load(R/f'IMAGING/HUBO-{pid}_structure.npz');aff=z['fa_affine'];shape=z['fa'].shape
  assert np.allclose(aff[:3,:3],np.diag(np.diag(aff[:3,:3]))) and all(np.array_equal(aff,z[k]) for k in ['left_affine','right_affine'])
  world=[aff[i,i]*np.arange(shape[i])+aff[i,3] for i in range(3)];order=[np.argsort(v) for v in world];world=[v[ix] for v,ix in zip(world,order)];arr={k:z[k][np.ix_(*order)] for k in ['fa','mask_left','mask_right']}
  for vi,view in enumerate(['axial','coronal']):
   ix=int(a[view+'_index']);ys=world[1 if vi==0 else 2];xs=world[0];raw={k:(v[:,:,ix] if vi==0 else v[:,ix,:]) for k,v in arr.items()};dx=xs[1]-xs[0];dy=ys[1]-ys[0];ex=[xs[0]-dx/2,xs[-1]+dx/2,ys[0]-dy/2,ys[-1]+dy/2]
   cx=np.searchsorted(xs,a['x_mm']);cy=np.searchsorted(ys,a['axial_y_mm' if vi==0 else 'coronal_z_mm'])
   for k,ck in [('fa','FA'),('mask_left','left_CST'),('mask_right','right_CST')]:assert np.array_equal(raw[k][np.ix_(cx,cy)],a[ck+'_'+view])
   crop=[-55,55,-55,55] if vi==0 else [-55,55,-35,75];ovlim=[-130,130,-110,155] if vi==0 else [-130,130,-80,90]
   y=124 if vi==0 else 43;oy=180 if vi==0 else 100;ow=26.4;oh=ow*(ovlim[3]-ovlim[2])/260
   overview=ax(f,x+(48-ow)/2,oy,ow,oh);detail=ax(f,x,y,48,48)
   for aa in [overview,detail]:pixels(aa,raw['fa'],ex,raw['mask_left'],raw['mask_right'])
   overview.set(xlim=ovlim[:2],ylim=ovlim[2:]);detail.set(xlim=crop[:2],ylim=crop[2:])
   overview.add_patch(Rectangle(crop[::2],110,110,fill=False,edgecolor=LINK,lw=.7));detail.add_patch(Rectangle(crop[::2],110,110,fill=False,edgecolor=LINK,lw=.7))
   for xx in crop[:2]:f.add_artist(ConnectionPatch((xx,crop[2]),(xx,crop[3]),coordsA=overview.transData,coordsB=detail.transData,color=LINK,lw=.5,zorder=.5,clip_on=False))
   letter=chr(97+2*pi+vi);tx(f,x-1,oy+oh-5,letter,fontsize=8,fontweight='bold');tx(f,x+(24 if vi==0 else 1),oy+oh+2,['Axial','Coronal'][vi],fontsize=8,ha='center' if vi==0 else 'left');tx(f,x-4,y+49,letter+'′',fontsize=9,fontweight='bold')
   direction(overview,view,50,True);direction(detail,view,20)
   axes.extend([overview,detail]);checks.append({'patient':pid,'view':view,'native_and_cached_pixels_equal':True,'slice_index':ix,'crop_mm':crop,'overview_mm':ovlim,'magnification':(48/110)/(26.4/260),'color_limits_FA':[0,.8],'interpolation':'nearest'})
  f.add_artist(plt.Line2D([x/180,(x+48)/180],[29/220]*2,transform=f.transFigure,color='#cbd2d7',lw=.6))
  for j,(col,lab,mult,fmt) in enumerate([('volume_mm3','体积（mm³）',1,'.2f'),('mean_FA','FA',1,'.4f'),('mean_MD','MD（10⁻³ mm²/s）',1000,'.4f')]):
   yq=24-j*8;v=q[q.patient_id=='HUBO-'+pid].set_index('side');tx(f,x,yq,lab,fontsize=8);tx(f,x+30,yq-3,f"{v.loc['Left',col]*mult:{fmt}}",ha='right',fontsize=8,color=LC);tx(f,x+49,yq-3,f"{v.loc['Right',col]*mult:{fmt}}",ha='right',fontsize=8,color=RC)
 rows=[];cols=[]
 for vi in range(2):
  for role in range(2):rows.append({'panels':[str(pi*4+vi*2+role) for pi in range(3)]})
 for pi in range(3):cols.append({'panels':[str(pi*4+1),str(pi*4+3)]})
 export(f,'Figure_2_FA_CST',axes=axes,rows=rows,cols=cols,sources=['native structure NPZ; unchanged selected-slice indices','IMAGING_CST_quantitative_reused.csv'])
 js(O/'RUN_RECORDS/CST_display.json',checks)

def old_plot_suite():
 # Reuse the original plotting functions and exact source tables. Alter display constants only.
 p=Path(__file__).parent/'frozen_plot_suite.py'
 spec=importlib.util.spec_from_file_location('style_plots',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 original=pd.read_csv
 def exact(*args,**kw):kw.setdefault('float_precision','round_trip');return original(*args,**kw)
 m.pd.read_csv=exact
 for fn in [m.response,m.differences,m.relations,m.pooled,m.pac,m.other_tfr,m.baseline_supp]:fn();print(fn.__name__,flush=True)
 m.pd.read_csv=original
 manifest.extend(m.manifest)
 # S4/S6: existing valid image geometry, no numeric rendering changes; labels enlarged.
 ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
 import re
 for stem in ['Figure_S4_registration','Figure_S6_surface_overview_detail']:
  root=ET.parse(OLD/'ASSETS'/f'{stem}.svg').getroot()
  for e in root.iter('{'+ns+'}text'):
   st=e.get('style','');ma=re.search(r'font-size: ([0-9.]+)px',st)
   if ma:st=re.sub(r'font-size: [0-9.]+px',f'font-size: {max(8,float(ma[1])):g}px',st);e.set('style',st)
  p=O/'FIGURES_SUPPLEMENTARY_EN'/f'{stem}.svg';translate_svg(root);ET.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True)
  cairosvg.svg2pdf(url=str(p),write_to=str(p.with_suffix('.pdf')));cairosvg.svg2png(url=str(p),write_to=str(p.with_suffix('.png')),scale=450/96)
  js(Q/f'{stem}_alignment_provenance.json',{'same_geometry':True,'source':str((OLD/'ASSETS'/f'{stem}.svg').relative_to(R)),'edit':'text font size only'})
  manifest.append({'stem':stem,'sources':[str((OLD/'ASSETS'/f'{stem}.svg').relative_to(R))],'raster_and_paths_unchanged':True})

def f6():
 f=plt.figure(figsize=(260/25.4,157/25.4));axes=[]
 tx(f,4,151,'a  P07：已确认的条带与通道',fontsize=10,fontweight='bold')
 for s in range(3):
  tx(f,64,151-s*6,f'条带{s+1}',fontsize=8)
  for k in range(1,9):
   ch=f'C{s*8+k}';tx(f,153-(k-1)*9,151-s*6,ch if ch in CH else '□',ha='center',fontsize=8)
 tx(f,169,151,'右→左：触点1→8',fontsize=8);tx(f,169,143,'□ 未记录；仅表示顺序，无毫米坐标',fontsize=8,color=GRAY)
 f.add_artist(plt.Line2D([.5,.5],[.095,.83],transform=f.transFigure,color='#cbd5da',lw=.8))
 for mi,(metric,title,scale,unit) in enumerate([('beta_same_scale','β任务前后变化',1,'dB'),('pac_full','校正PAC',1000,'MI × 10⁻³')]):
  off=mi*130;lim=LIM['static_shared_limits'][metric];tx(f,5+off,129,['b  ','c  '][mi]+title,fontsize=10,fontweight='bold')
  for ci in range(3):tx(f,36.5+off+ci*37,120,SCN[ci],fontsize=8.5,ha='center')
  for ai,act in enumerate(ACTS):
   y=101-ai*18;tx(f,3+off,y+5.5,CN[ai],fontsize=9,va='center')
   for ci,state in enumerate(STATE):
    a=ax(f,19+off+ci*37,y,35,13);v={k:n*scale for k,n in vals(S[S.action==act],metric,state).items()};array(a,v,lim,True);axes.append(a)
  bar(f,25+off,15,68,lim,unit)
 tx(f,4,2,'每个色块对应一个原通道值；22个记录触点与2个空白触点完整保留。每动作每状态6事件，患者 n = 1。',fontsize=8,color=GRAY)
 rows=[{'panels':[str(mi*15+ai*3+ci) for ci in range(3)]} for mi in range(2) for ai in range(5)];cols=[{'panels':[str(mi*15+ai*3+ci) for ai in range(5)]} for mi in range(2) for ci in range(3)]
 export(f,'Figure_6_P07_static_array',axes=axes,rows=rows,cols=cols,sources=['P07_static_arrays.csv','P07_contact_topology.csv'])
def f7():
 f=plt.figure(figsize=(260/25.4,166/25.4));axes=[];xl,xr=16,250;step=(xr-xl)/7;start=xl+2*step;lim=LIM['pooled_beta_shared_limit']
 for w in range(5):
  left=start+w*step;f.add_artist(Rectangle((left/260,16/166),step/260,130/166,transform=f.transFigure,facecolor=['#eff4f6','#fafbfc'][w%2],edgecolor='none',zorder=-10));tx(f,left+step/2,149,f'{w}–{w+1} s',ha='center',fontsize=9)
 tx(f,5,160,'a  五个固定任务窗中的β阵列',fontsize=10,fontweight='bold');tx(f,12,140,'五动作合并',fontsize=8);tx(f,12,133,'每状态30事件',fontsize=8,color=GRAY)
 for ci,state in enumerate(STATE):
  y=116-ci*21;tx(f,14,y+6,SCN[ci],fontsize=9)
  for w in range(5):
   a=ax(f,start+w*step+1,y,step-2,19);v=vals(P[P.window_start_s==w],'beta_M1_db',state);array(a,v,lim,False,True,True);axes.append(a)
 bar(f,15,92,38,lim,'dB');tx(f,14,70,'细框：固定通道 C2',fontsize=8,color=GRAY)
 tx(f,5,65,'b  相同通道 C2 的完整时程',fontsize=10,fontweight='bold');tx(f,176,65,'执行',fontsize=9,color=BLUE);tx(f,208,65,'想象',fontsize=9,color=ORANGE)
 curve=ax(f,xl,16,xr-xl,42);k=CH.index('C2');yl=float(np.ceil(np.max(np.abs(C[:,k])))) or 1
 curve.set_facecolor('none');curve.axvspan(-2,0,color='#f0f0f0',zorder=0);curve.axhline(0,color='#8798a0',lw=.5)
 for w in range(6):curve.axvline(w,color='#cad5db',lw=.55,zorder=0)
 for ci,color in enumerate([BLUE,ORANGE]):curve.plot(T,C[ci,k],color=color,lw=1)
 curve.set(xlim=(-2,5),ylim=(-yl,yl),xticks=list(range(-2,6)),yticks=[-yl,0,yl],ylabel='β变化（dB）');curve.tick_params(labelsize=8,pad=2,length=3)
 tx(f,49.4,59,'任务前基线',ha='center',fontsize=8,color=GRAY);tx(f,250,6,'时间（s）',ha='right',fontsize=8)
 # Subtle bracket leads the identified C2 to its paired curve; no anatomical claim.
 f.add_artist(plt.Line2D([47/260,51/260,51/260],[70/166,70/166,66.5/166],transform=f.transFigure,color='#677780',lw=.6,zorder=.4))
 tx(f,5,1,'上方窗图与下方时程共用时间分区；全部通道及五动作见图S9–S11。色标与原版一致。',fontsize=8,color=GRAY)
 f.set_size_inches(260/25.4,160/25.4)
 rows,cols=gridgroups(3,5);export(f,'Figure_7_P07_dynamic_array',axes=axes,rows=rows,cols=cols,sources=['P07_pooled_dynamic_windows.csv','P07_pooled_beta_curves.npz'])
 js(Q/'Figure7_time_alignment.json',{'curve_xlim':[-2,5],'curve_bounds_mm':[xl,xr],'window_boundaries_mm':[start+w*step for w in range(6)],'C2_source_rule':'historical fixed source','unchanged_curve_samples':True})

def channel_grid(f,curves=None,tfrdata=None):
 axes=[];yl=float(np.ceil(np.max(np.abs(curves)))) or 1 if curves is not None else None
 for s in range(3):
  for con in range(1,9):
   ch=f'C{s*8+con}';col=8-con;a=ax(f,15+col*30,99-s*35,26.5,25);axes.append(a)
   if ch in CH:
    if curves is not None:
     a.axvspan(0,5,color='#f0f3f4',zorder=0);a.axhline(0,lw=.4,color='#999');a.axvline(0,lw=.4,color='#999')
     for ci,color in enumerate([BLUE,ORANGE]):a.plot(T,curves[ci,CH.index(ch)],color=color,lw=.7)
    else:
     dat,freq,lim=tfrdata;a.imshow(dat[CH.index(ch)],origin='lower',aspect='auto',extent=[T[0],T[-1],freq[0],freq[-1]],cmap=CM,vmin=-lim,vmax=lim,interpolation='nearest',rasterized=True);a.axvline(0,color='#444',lw=.4)
    a.set_title(ch,fontsize=8,pad=3)
   else:a.text(.5,.5,'未记录',transform=a.transAxes,ha='center',va='center',fontsize=8);a.set_title('触点'+str(con),fontsize=8,pad=3)
   a.set(xlim=(-2,5),ylim=(-yl,yl) if curves is not None else (4,90),xticks=[-2,0,5],yticks=[-yl,0,yl] if curves is not None else [4,30,90]);a.tick_params(labelsize=8,pad=2,length=2)
   if col:a.set_yticklabels([])
   if s<2:a.set_xticklabels([])
  tx(f,3,111-s*35,f'条带{s+1}',rotation=90,fontsize=8,va='center')
 return axes

def si_grids():
 z=np.load(AROOT/'P07_allchannel_TFR_display.npz');lim=float(np.max(np.abs(z['values_db'])))
 for ci,c in enumerate(STATE[:2]):
  f=plt.figure(figsize=(260/25.4,147/25.4));tx(f,5,139,'P07 · '+SCN[ci]+'：全通道时频反应',fontsize=10,fontweight='bold')
  aa=channel_grid(f,tfrdata=(z['values_db'][ci],z['frequencies_hz'],lim));bar(f,84,12,75,lim,'功率（dB）');tx(f,5,1,'横轴：时间（s）；纵轴：频率（Hz）。沿用原4–90 Hz数组；每状态30事件，原共享色标。',fontsize=8,color=GRAY)
  rows,cols=gridgroups(3,8);export(f,f'Figure_S{7+ci}_P07_allchannel_TFR_{c}',False,aa,rows,cols,['P07_allchannel_TFR_display.npz'])
 for ai,action in enumerate(ACTS+['pooled']):
  cc=C if action=='pooled' else AZ['values_db'][AZ['actions'].tolist().index(action)]
  f=plt.figure(figsize=(260/25.4,140/25.4));tx(f,5,132,'P07 · '+('五动作合并' if action=='pooled' else CN[ai])+'：全部22通道时程',fontsize=10,fontweight='bold');tx(f,197,132,'执行',fontsize=9,color=BLUE);tx(f,230,132,'想象',fontsize=9,color=ORANGE)
  aa=channel_grid(f,curves=cc);tx(f,5,7,'横轴：时间（s）；纵轴：β变化（dB）。灰底为任务期，未记录触点留空；所有已保存时点完整显示。',fontsize=8,color=GRAY)
  rows,cols=gridgroups(3,8);stem='Figure_S11_P07_pooled_timecourses' if action=='pooled' else f'Figure_S9{chr(97+ai)}_P07_timecourse_{action}'
  export(f,stem,False,aa,rows,cols,['P07_pooled_beta_curves.npz' if action=='pooled' else 'P07_beta_display_curves.npz'])
 # S10 from saved five-window table (never recompute a window from timeseries).
 for ai,action in enumerate(ACTS):
  f=plt.figure(figsize=(260/25.4,122/25.4));tx(f,5,115,f'P07 · {CN[ai]}：五个固定1秒窗中的β阵列',fontsize=10,fontweight='bold');aa=[];lim=LIM['action_beta_shared_limit']
  for wi in range(5):tx(f,49+wi*45,103,f'{wi}–{wi+1} s',ha='center',fontsize=9)
  for ci,state in enumerate(STATE):
   y=78-ci*24;tx(f,3,y+8,SCN[ci],fontsize=9)
   for wi in range(5):
    a=ax(f,29+wi*45,y,40,18);v=vals(D[(D.action==action)&(D.window_start_s==wi)],'beta_M1_db',state);array(a,v,lim,True);aa.append(a)
  bar(f,78,15,85,lim,'β变化（dB）');tx(f,5,1,'同一通道顺序；两个未记录触点留空。五动作、状态与差值共享原色标；每状态6事件。',fontsize=8,color=GRAY)
  rows,cols=gridgroups(3,5);export(f,f'Figure_S10{chr(97+ai)}_P07_dynamic_{action}',False,aa,rows,cols,['P07_beta_dynamic_windows.csv'])

def animation():
 frames=[];lim=LIM['action_beta_shared_limit']
 for wi in range(5):
  f=plt.figure(figsize=(180/25.4,183/25.4));tx(f,5,175,'P07 · β阵列的五窗逐帧展示',fontsize=11,fontweight='bold');tx(f,5,166,f'当前任务窗：{wi}–{wi+1} s',fontsize=10,fontweight='bold');aa=[]
  for k in range(5):
   f.add_artist(Rectangle(((88+k*16)/180,164/183),14/180,8/183,transform=f.transFigure,facecolor='#395e70' if k==wi else '#edf1f3',edgecolor='none'));tx(f,95+k*16,166,f'{k}–{k+1}',ha='center',fontsize=8,color='white' if k==wi else GRAY)
  for ci in range(3):tx(f,46+ci*49,155,SCN[ci],ha='center',fontsize=9)
  for ai,action in enumerate(ACTS):
   y=131-ai*24;tx(f,4,y+7,CN[ai],fontsize=9)
   for ci,state in enumerate(STATE):
    a=ax(f,23+ci*49,y,46,17);array(a,vals(D[(D.action==action)&(D.window_start_s==wi)],'beta_M1_db',state),lim,True);aa.append(a)
  bar(f,38,23,75,lim,'β变化（dB）');tx(f,5,8,'22个记录触点与2个空白；五动作共享固定色标。',fontsize=8,color=GRAY);tx(f,5,1,'仅播放原五个1秒窗；无插帧，无动态PAC。',fontsize=8,color=GRAY)
  f.canvas.draw();rows,cols=gridgroups(5,3);require_matplotlib_panel_alignment(f,axes=aa,panel_ids=[str(i) for i in range(15)],row_groups=rows,column_groups=cols,json_out=Q/f'Animation_{wi}_alignment.json',strict=True)
  p=O/f'ANIMATION/FRAMES/beta_window_{wi}_{wi+1}.png';f.savefig(p,dpi=300);plt.close(f);frames.append(Image.open(p).convert('RGB'))
 w,h=frames[0].size;sheet=Image.new('RGB',(w,h*5))
 for i,im in enumerate(frames):sheet.paste(im,(0,i*h))
 palette=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT);ff=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames];p=O/'ANIMATION/P07_beta_five_windows.gif';ff[0].save(p,save_all=True,append_images=ff[1:],duration=[1000]*5,loop=0,disposal=2,optimize=False)
 js(O/'RUN_RECORDS/animation.json',{'frames':5,'ms_per_frame':1000,'source':'P07_beta_dynamic_windows.csv','shared_limit_db':lim,'shared_palette':True,'new_timepoints':0,'display':'same strip matrices as Figure S10'})
if __name__=='__main__':
 selected=sys.argv[1:] or ['f1','f2','old_plot_suite','f6','f7','si_grids','animation']
 for name in selected:globals()[name]();print(name+' complete',flush=True)
 js(O/'RUN_RECORDS/figure_manifest.json',manifest)

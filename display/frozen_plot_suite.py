"""Five main and five supplementary figures from verified local arrays/tables.
No data are reconstructed from legacy graphics. Run with /opt/anaconda3/bin/python.
"""
from pathlib import Path
import os,sys,json
from datetime import datetime,timezone
O=Path(os.environ['NCS_DISPLAY_OUT']);R=Path(os.environ['NCS_DISPLAY_INPUT']);S=R/'SOURCE_DATA';Q=O/'QA'
os.environ['MPLCONFIGDIR']=str(O/'RUN_RECORDS/mpl_cache')
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch,Patch
from matplotlib import font_manager
from matplotlib.colors import ListedColormap
from english_labels import install,fit_labels
install()
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'figure.facecolor':'white','savefig.facecolor':'white'})
from layout_check import require_matplotlib_panel_alignment
IDS=['HUBO-P07','HUBO-P04','HUBO-P08','HUBO-P10'];ACTS=['fingerLeft','fingerRight','fistLeft','fistRight','lip'];AL=['左指','右指','左拳','右拳','唇部']
COL={'Move':'#356B91','Imagine':'#B56E3C'};PC=['#356B91','#AF6940','#52795D','#876B91'];AC=['#356B91','#B17745','#57785D','#876B91','#666666'];LC='#2A7894';RC='#C48243'
manifest=[]
def mm(w,h):return (w/25.4,h/25.4)
def lab(ax,s):ax.set_title(s,loc='left',fontweight='bold',fontsize=10,pad=9)
def save(fig,key,name,sources,purpose,multi=True):
    fit_labels(fig);fig.canvas.draw()
    if multi:require_matplotlib_panel_alignment(fig,json_out=Q/(name+'_alignment.json'),strict=True)
    else:(Q/(name+'_alignment.json')).write_text(json.dumps({'status':'not applicable','reason':'single schematic canvas'}))
    F=O/('FIGURES_SUPPLEMENTARY_EN' if key.startswith('S') else 'FIGURES_MAIN_EN')
    fig.savefig(F/(name+'.pdf'))
    fig.savefig(F/(name+'.svg'))
    fig.savefig(F/(name+'.png'),dpi=450)
    manifest.append({'figure':key,'stem':name,'sources':sources,'purpose':purpose,'size_mm':[round(float(v)*25.4,2) for v in fig.get_size_inches()],'panels':len([a for a in fig.axes if a.get_label()!='<colorbar>'])})
    plt.close(fig)

def design():
    fig,ax=plt.subplots(figsize=mm(180,146));fig.subplots_adjust(0,0,1,1);ax.set(xlim=(0,180),ylim=(0,146));ax.axis('off')
    def txt(x,y,t,**kw):ax.text(x,y,t,va='center',fontsize=kw.pop('fontsize',9),**kw)
    def box(x,y,w,h,title,lines,col):
        ax.add_patch(Rectangle((x,y),w,h,facecolor='white',edgecolor='#AAB4BC',lw=.8));txt(x+4,y+h-6,title,fontweight='bold',color=col,fontsize=10);txt(x+4,y+h-18,lines,linespacing=1.6)
    def arr(x,y,x2,y2):ax.add_patch(FancyArrowPatch((x,y),(x2,y2),arrowstyle='-|>',mutation_scale=11,color='#77818A',lw=.9))
    txt(5,139,'a  临床来源与实际分析对象',fontweight='bold',fontsize=11)
    box(5,100,48,29,'临床来源  11例','10例胶质瘤谱系\n1例非胶质瘤', '#333333')
    box(66,100,50,29,'CST结构  3例','P01 · P06 · P07\n真实FA与双侧掩膜', '#526A63')
    box(127,100,48,29,'ECoG  4例','P07 · P04 · P08 · P10\n91通道 · 210事件',COL['Move'])
    arr(54,115,64,115);ax.plot([29,29,151],[100,96,96],color='#77818A',lw=.9);arr(151,96,151,99.5)
    txt(66,88,'两类分析共享P07；独立患者合计6例',fontweight='bold')
    txt(5,78,'任务fMRI显示材料尚不足以给出连续任务效应；可靠空间配对为0。',color='#555555')
    txt(5,66,'b  执行与想象的重复测量',fontweight='bold',fontsize=11)
    txt(5,55,'左指 · 右指 · 左拳 · 右拳 · 唇部')
    txt(5,46,'每轮5动作 × 2状态 = 10事件')
    txt(5,37,'P07：6轮；其余患者：5轮')
    x0=97;sc=10
    ax.add_patch(Rectangle((x0,45),20,7,facecolor='#E3E6E8',edgecolor='none'))
    ax.add_patch(Rectangle((x0+20,45),50,7,facecolor='#D8E5ED',edgecolor='none'))
    for t in [-2,0,5]:
        x=x0+(t+2)*sc;ax.plot([x,x],[43,53],color='#444444',lw=.8);txt(x,38,str(t),ha='center')
    txt(107,59,'基线',ha='center');txt(142,59,'任务',ha='center');txt(175,38,'秒',ha='center')
    txt(5,24,'c  主要比较保留患者、动作与通道',fontweight='bold',fontsize=11)
    txt(5,14,'同通道：Δβ功率  ↔  Δ校正PAC；Δ = 想象 − 执行')
    txt(5,5,'接线身份、物理触点、影像空间位置分别确认；术前与术中不作逐秒对齐。',fontsize=8.5,color='#555555')
    save(fig,'1','Figure_1_design',['MANUSCRIPT_case_pairing_coverage_reused.csv','MULTIMODAL_channel_action_trace.csv'],'study, timing and unit schematic',False)

def extent(a,view):
    x=a['x_mm'];y=a['axial_y_mm' if view=='axial' else 'coronal_z_mm']
    dx=np.diff(x).mean();dy=np.diff(y).mean()
    return [x[0]-dx/2,x[-1]+dx/2,y[0]-dy/2,y[-1]+dy/2]

def image_panel(ax,a,view,overlay=True,kind='FA'):
    arr=a[kind+'_'+view]; ex=extent(a,view)
    assert np.isfinite(arr).all()
    limits=(0,.8) if kind=='FA' else tuple(a['T1_display_intensity_clip'])
    ax.imshow(arr.T,origin='lower',extent=ex,cmap='gray',vmin=limits[0],vmax=limits[1],interpolation='nearest')
    if overlay:
        masks=[a['left_CST_'+view].astype(bool),a['right_CST_'+view].astype(bool)]
        assert all(m.shape==arr.shape for m in masks)
        z=masks[0].astype(int)+2*masks[1].astype(int)
        ax.imshow(np.ma.masked_equal(z.T,0),origin='lower',extent=ex,cmap=ListedColormap([LC,RC,'#806590']),vmin=.5,vmax=3.5,interpolation='nearest',alpha=.8)
    ax.set(xlim=(-55,55),ylim=(-55,55) if view=='axial' else (-35,75));ax.set_aspect('equal');ax.axis('off')
    ax.text(.02,.5,'L',transform=ax.transAxes,ha='left',va='center',fontsize=8,fontweight='bold',bbox=dict(facecolor='white',edgecolor='none',pad=.2))
    ax.text(.98,.5,'R',transform=ax.transAxes,ha='right',va='center',fontsize=8,fontweight='bold',bbox=dict(facecolor='white',edgecolor='none',pad=.2))
    ax.text(.5,.995,'A' if view=='axial' else 'S',transform=ax.transAxes,ha='center',va='top',fontsize=8,fontweight='bold',bbox=dict(facecolor='white',edgecolor='none',pad=.2))
    ax.text(.5,.005,'P' if view=='axial' else 'I',transform=ax.transAxes,ha='center',va='bottom',fontsize=8,fontweight='bold',bbox=dict(facecolor='white',edgecolor='none',pad=.2))
    # Every displayed view uses the same physical field of view and 20 mm bar.
    yy=-51 if view=='axial' else -31
    ax.plot([27,47],[yy,yy],color='#333333',lw=1.5,solid_capstyle='butt')
    ax.text(37,yy+2.3,'20 mm',ha='center',va='bottom',fontsize=7.5,bbox=dict(facecolor='white',edgecolor='none',pad=.3))

def cst():
    fig,axes=plt.subplots(3,2,figsize=mm(180,225))
    fig.subplots_adjust(left=.03,right=.97,top=.94,bottom=.06,hspace=.19,wspace=.12)
    names=[]
    for i,pid in enumerate(['P01','P06','P07']):
        f=f'IMAGING_HUBO-{pid}_deidentified_selected_slices.npz';a=np.load(S/f);names.append(f)
        for j,v in enumerate(['axial','coronal']):
            image_panel(axes[i,j],a,v);lab(axes[i,j],f'{chr(97+2*i+j)}  {pid}  '+['轴位','冠状位'][j])
    fig.legend(handles=[Patch(facecolor=LC,label='左侧CST'),Patch(facecolor=RC,label='右侧CST')],loc='upper center',bbox_to_anchor=(.5,1),ncol=2,frameon=False,fontsize=9)
    fig.text(.07,.012,'FA灰度：0–0.8；同一物理视野110 × 110 mm；患者各自的扩散影像空间。',fontsize=8)
    save(fig,'2','Figure_2_FA_CST',names,'three real FA backgrounds, bilateral masks and two orthogonal views each')

def tfr(ax,a,k,title):
    assert a[k].shape==(len(a['frequencies_hz']),len(a['times_s']))
    assert np.nanmax(np.abs(a[k]))<=20
    im=ax.pcolormesh(a['times_s'],a['frequencies_hz'],a[k],cmap='RdBu_r',vmin=-20,vmax=20,shading='auto',rasterized=True)
    ax.axvline(0,color='#555555',lw=.7,ls='--');ax.set(xlabel='时间（秒）',ylabel='频率（Hz）',ylim=(4,90),xlim=(-2,5),yticks=[13,30,60,90],xticks=[-2,0,2,5]);lab(ax,title)
    return im

def response():
    fig=plt.figure(figsize=mm(180,212));gs=fig.add_gridspec(3,2,left=.115,right=.87,top=.935,bottom=.105,hspace=.60,wspace=.35)
    a=np.load(S/'TASK_P08_C1_tfr.npz')
    for j,k in enumerate(['move_median_db','imagine_median_db']):
        ax=fig.add_subplot(gs[0,j]);im=tfr(ax,a,k,chr(97+j)+'  P08/C1  '+['执行','想象'][j])
    ca=fig.add_axes([.905,.717,.018,.21]);fig.colorbar(im,cax=ca,label='功率（dB）',ticks=[-20,0,20])
    d=pd.read_csv(S/'TEMPORAL_all_channel_beta_summary.csv.gz')
    lo=float(d.channel_q1_db.min());hi=float(d.channel_q3_db.max());yl=(np.floor(lo),np.ceil(hi))
    for i,pid in enumerate(IDS):
        ax=fig.add_subplot(gs[1+i//2,i%2]);v=d[d.patient_id==pid]
        for cond in ['Move','Imagine']:
            g=v[v.condition==cond].sort_values('time_s');x=g.time_s.to_numpy()
            ax.fill_between(x,g.channel_q1_db.to_numpy(),g.channel_q3_db.to_numpy(),color=COL[cond],alpha=.18,lw=0)
            ax.plot(x,g.channel_median_db,color=COL[cond],lw=1.15,label={'Move':'执行','Imagine':'想象'}[cond])
        ax.axvline(0,color='#666666',ls='--',lw=.6);ax.axhline(0,color='#AAAAAA',lw=.6)
        ax.set(xlim=(-2,5),ylim=yl,xlabel='时间（秒）',ylabel='β功率（dB）',xticks=[-2,0,2,5]);lab(ax,f'{chr(99+i)}  {pid[-3:]}  全部{int(v.n_channels.iloc[0])}通道')
    handles,labels=ax.get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.045),ncol=2,frameon=False)
    fig.text(.115,.015,'c–f：逐时点通道中位数及四分位范围；同批事件与基线，独立患者 n = 4。',fontsize=8)
    save(fig,'3','Figure_3_time_frequency',['TASK_P08_C1_tfr.npz','TEMPORAL_all_channel_beta_summary.csv.gz'],'frequency shape and all-channel temporal coverage')

def differences():
    e=pd.read_csv(S/'JOINT_patient_action_estimates.csv');c=pd.read_csv(S/'JOINT_channel_pairs.csv')
    q=e[e.condition=='Imagine_minus_Move'].set_index(['patient_id','action']);d=c[c.condition=='Imagine_minus_Move'];assert len(d)==455
    fig,axes=plt.subplots(1,2,figsize=mm(180,214),sharey=True);fig.subplots_adjust(left=.15,right=.975,top=.935,bottom=.115,wspace=.19)
    ys=[];labs=[]
    for pi,pid in enumerate(IDS):
        for ai,act in enumerate(ACTS):
            y=pi*6+ai;ys.append(y);labs.append(pid[-3:]+'  '+AL[ai]);r=q.loc[(pid,act)];g=d[(d.patient_id==pid)&(d.action==act)].sort_values('channel')
            dy=np.linspace(-.15,.15,len(g)) # determined only by channel identity
            for ax,col,pointcol,f in zip(axes,['beta','pac_original'],['beta_db','pac_original'],[1,1e4]):
                ax.scatter(g[pointcol]*f,y+dy,s=11,alpha=.34,facecolor=PC[pi],edgecolor='none',zorder=1)
                low=r[col+'_ci_low']*f;high=r[col+'_ci_high']*f
                ax.hlines(y,low,high,color=PC[pi],lw=1.2,zorder=2);ax.plot([low,high],[y,y],'|',color=PC[pi],ms=4,zorder=2)
                ax.scatter(r[pointcol]*f,y,s=24,facecolor=PC[pi],edgecolor='white',linewidth=.4,zorder=3)
    for ax in axes:
        ax.axvline(0,color='#777777',ls='--',lw=.7);ax.set_ylim(23,-1);ax.set_yticks(ys,labs);ax.tick_params(axis='y',length=0)
        for y in [5,11,17]:ax.axhline(y,color='#DDDDDD',lw=.7)
    # Retain every observed channel value as well as all long conditional ranges.
    for ax,col,ci,f in zip(axes,['beta_db','pac_original'],['beta','pac_original'],[1,1e4]):
        v=np.r_[d[col].to_numpy()*f,q[ci+'_ci_low'].to_numpy()*f,q[ci+'_ci_high'].to_numpy()*f];pad=(v.max()-v.min())*.07;ax.set_xlim(v.min()-pad,v.max()+pad)
    axes[0].set_xlabel('Δβ功率（dB）');axes[1].set_xlabel('Δ校正PAC（10⁻⁴ MI）');lab(axes[0],'a  β功率');lab(axes[1],'b  校正PAC')
    fig.text(.15,.057,'小点：全部通道；大点：同通道差值的中位数；线段：95%条件范围。',fontsize=8)
    fig.text(.15,.027,'Δ = 想象 − 执行；每行21–24通道；20个患者–动作单元来自4名患者。',fontsize=8)
    save(fig,'4','Figure_4_patient_action',['JOINT_channel_pairs.csv','JOINT_patient_action_estimates.csv'],'all channel distributions and uncertainty within patient and action')

def relations():
    c=pd.read_csv(S/'JOINT_channel_pairs.csv');p=pd.read_csv(S/'JOINT_patient_associations.csv')
    fig=plt.figure(figsize=mm(180,213));gs=fig.add_gridspec(3,2,left=.12,right=.965,top=.945,bottom=.155,hspace=.64,wspace=.34,height_ratios=[1,1,.9]);axes=[]
    for i,pid in enumerate(IDS):
        ax=fig.add_subplot(gs[i//2,i%2]);axes.append(ax);g=c[(c.patient_id==pid)&(c.condition=='Imagine_minus_Move')]
        for j,act in enumerate(ACTS):
            v=g[g.action==act];ax.scatter(v.beta_db,v.pac_original*1e4,s=18,alpha=.68,edgecolors='none',color=AC[j],label=AL[j])
        ax.axhline(0,color='#BBBBBB',lw=.6);ax.axvline(0,color='#BBBBBB',lw=.6);ax.set(xlabel='Δβ功率（dB）',ylabel='ΔPAC（10⁻⁴ MI）');lab(ax,f'{chr(97+i)}  {pid[-3:]}  {len(g)}个配对')
    ax=fig.add_subplot(gs[2,:]);q=p[(p.comparison=='Imagine_minus_Move')&(p.grid=='original')].set_index('patient_id')
    for i,pid in enumerate(IDS):
        r=q.loc[pid];ax.hlines(i,r.rho_ci_low,r.rho_ci_high,color=PC[i],lw=1.3);ax.scatter(r.rho,i,s=30,color=PC[i],zorder=3)
    ax.axvline(0,color='#999999',ls='--',lw=.7);ax.set(yticks=range(4),yticklabels=[x[-3:] for x in IDS],xlim=(-.4,.4),ylim=(3.6,-.7),xlabel='每患者五个动作特异Spearman ρ的中位数');lab(ax,'e  患者内的分层关联及95%条件范围')
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.54,.052),ncol=5,frameon=False,fontsize=9)
    fig.text(.12,.022,'a–d：坐标范围随患者变化；每通道重复参与5动作；患者为独立单位，n = 4。',fontsize=8)
    save(fig,'5','Figure_5_power_PAC',['JOINT_channel_pairs.csv','JOINT_patient_associations.csv'],'direct same-channel differences and stratified associations')

def pooled():
    p=pd.read_csv(S/'TASK_all_channel_pooled_beta.csv');fig,axes=plt.subplots(2,2,figsize=mm(180,165));fig.subplots_adjust(left=.12,right=.97,top=.93,bottom=.13,hspace=.43,wspace=.28)
    for i,(ax,pid) in enumerate(zip(axes.flat,IDS)):
        g=p[p.record_id==pid].pivot(index='channel_slot',columns='condition',values='task_mean_of_trial_median_db');assert g.notna().all().all()
        dx=np.linspace(-.1,.1,len(g))
        for j,row in enumerate(g.itertuples()):ax.plot([0+dx[j],1+dx[j]],[row.Move,row.Imagine],color='#BDC5CC',lw=.6,zorder=1)
        for j,cond in enumerate(['Move','Imagine']):
            v=g[cond].to_numpy();ax.scatter(j+dx,v,color=COL[cond],s=15,alpha=.8,zorder=2);ax.plot([j-.16,j+.16],[np.median(v)]*2,color='#222222',lw=1.7,zorder=3)
        ax.axhline(0,color='#999999',ls='--',lw=.7);ax.set(xticks=[0,1],xticklabels=['执行','想象'],ylim=(-6,.5),xlim=(-.4,1.4),ylabel='任务期β功率（dB）');lab(ax,f'{chr(97+i)}  {pid[-3:]}  {len(g)}通道')
    fig.text(.12,.045,'点为全部通道，灰线连接同通道条件，黑横线为通道中位数。',fontsize=9)
    fig.text(.12,.014,'原对数摘要的负值不等同于同尺度任务−基线下降；敏感性检查见图S5。',fontsize=8.5)
    save(fig,'S1','Figure_S1_pooled_beta',['TASK_all_channel_pooled_beta.csv'],'pooled action beta endpoint coverage and same-channel pairing')

def pac():
    d=pd.read_csv(S/'TASK_P08_C1_corrected_PAC_grid.csv');mats=[]
    for cond in ['Move','Imagine']:mats.append(d[d.condition==cond].pivot(index='amplitude_center_hz',columns='phase_center_hz',values='corrected_MI').to_numpy()*1e4)
    bound=float(np.ceil(max(np.abs(m).max() for m in mats)*10)/10)
    fig,axes=plt.subplots(1,2,figsize=mm(180,92));fig.subplots_adjust(left=.105,right=.865,bottom=.25,top=.8,wspace=.33)
    for j,ax in enumerate(axes):
        im=ax.imshow(mats[j],origin='lower',extent=[14,30,70,90],aspect='auto',cmap='RdBu_r',vmin=-bound,vmax=bound,interpolation='nearest');ax.set(xticks=[15,19,23,27,29],yticks=[75,85],xlabel='相位中心（Hz）',ylabel='幅度中心（Hz）');lab(ax,chr(97+j)+'  P08/C1  '+['执行','想象'][j])
    ca=fig.add_axes([.9,.25,.017,.55]);fig.colorbar(im,cax=ca,label='任务减基线PAC（10⁻⁴ MI）')
    save(fig,'S2','Figure_S2_PAC_frequency',['TASK_P08_C1_corrected_PAC_grid.csv'],'unaggregated fixed-source PAC frequency grid')

def other_tfr():
    fig,axes=plt.subplots(3,2,figsize=mm(180,215));fig.subplots_adjust(left=.115,right=.865,top=.935,bottom=.10,hspace=.55,wspace=.35);names=[]
    for i,(pid,ch) in enumerate([('HUBO-P07','C2'),('HUBO-P04','C1'),('HUBO-P10','C1')]):
        fn=f'TASK_{pid}_{ch}_tfr.npz';a=np.load(S/fn);names.append(fn)
        for j,k in enumerate(['move_median_db','imagine_median_db']):im=tfr(axes[i,j],a,k,f'{chr(97+2*i+j)}  {pid[-3:]}/{ch}  '+['执行','想象'][j])
    ca=fig.add_axes([.905,.10,.018,.835]);fig.colorbar(im,cax=ca,label='相对基线功率（dB）',ticks=[-20,-10,0,10,20]);fig.text(.115,.027,'固定来源通道；色标与图3a、b一致；每行是同一患者的两个条件。',fontsize=8)
    save(fig,'S3','Figure_S3_other_TFR',names,'fixed-source time-frequency shape in remaining three patients')

def registration():
    fig,axes=plt.subplots(2,2,figsize=mm(180,174));fig.subplots_adjust(left=.045,right=.97,top=.94,bottom=.075,hspace=.22,wspace=.15);names=[]
    for i,pid in enumerate(['P06','P07']):
        fn=f'IMAGING_HUBO-{pid}_deidentified_selected_slices.npz';a=np.load(S/fn);names.append(fn)
        for j,kind in enumerate(['T1','FA']):
            image_panel(axes[i,j],a,'axial',False,kind);lab(axes[i,j],f'{chr(97+2*i+j)}  {pid}  {kind}  相同世界层面')
    fig.text(.07,.02,'几何头信息相容，实际解剖仍不一致；FA对照复用图2相同层面。',fontsize=9)
    save(fig,'S4','Figure_S4_registration',names,'anatomical registration limitation, shared FA controls explicitly reused')


def baseline_supp():
    pooled=pd.read_csv(S/'BASELINE_pooled_channels.csv');a=pd.read_csv(S/'BASELINE_patient_action.csv');p=pd.read_csv(S/'BASELINE_patient_rho.csv')
    fig=plt.figure(figsize=mm(180,195));gs=fig.add_gridspec(2,2,left=.14,right=.97,top=.94,bottom=.205,hspace=.53,wspace=.50,height_ratios=[.8,1.4])
    ax=fig.add_subplot(gs[0,:])
    for i,pid in enumerate(IDS):
        g=pooled[pooled.patient_id==pid].pivot(index='channel',columns='condition',values='centered_task_minus_baseline_db');dx=np.linspace(-.10,.10,len(g))
        for k,row in enumerate(g.itertuples()):ax.plot([i-.15+dx[k],i+.15+dx[k]],[row.Move,row.Imagine],color='#C5CCD1',lw=.5)
        for cond,off in [('Move',-.15),('Imagine',.15)]:
            ax.scatter(i+off+dx,g[cond],color=COL[cond],s=10,alpha=.75,label={'Move':'执行','Imagine':'想象'}[cond] if i==0 else None)
            ax.plot([i+off-.10,i+off+.10],[g[cond].median()]*2,color='#222222',lw=1.5)
    ax.axhline(0,color='#777777',ls='--',lw=.7);ax.set(xticks=range(4),xticklabels=[x[-3:] for x in IDS],ylabel='任务−基线（dB）',ylim=(-2.8,1.4));ax.legend(loc='lower left',ncol=2,frameon=False,fontsize=8);lab(ax,'a  合并动作后的同尺度β变化')
    ax=fig.add_subplot(gs[1,0]);mat=[];labels=[]
    for pid in IDS:
        for act,al in zip(ACTS,AL):
            g=a[(a.patient_id==pid)&(a.action==act)].set_index('condition');mat.append([g.loc[c,'centered_beta_db'] for c in ['Move','Imagine']]);labels.append(pid[-3:]+' '+al)
    mat=np.array(mat);im=ax.imshow(mat,origin='upper',aspect='auto',cmap='RdBu_r',vmin=-2.1,vmax=2.1)
    ax.set(yticks=range(20),yticklabels=labels,xticks=[0,1],xticklabels=['执行','想象']);ax.tick_params(length=0)
    for y in [4.5,9.5,14.5]:ax.axhline(y,color='white',lw=2)
    for i in range(20):
        for j in range(2):ax.text(j,i,f'{mat[i,j]:+.2f}',ha='center',va='center',fontsize=7.5,color='white' if abs(mat[i,j])>1.3 else '#222222')
    lab(ax,'b  患者–动作中位数（dB）')
    ax=fig.add_subplot(gs[1,1]);g=p[p.comparison=='Imagine_minus_Move']
    for i,pid in enumerate(IDS):
        for grid,dy,color,marker in [('original',-.12,'#356B91','o'),('70_90',.12,'#B56E3C','s')]:
            r=g[(g.patient_id==pid)&(g.grid==grid)].iloc[0];ax.hlines(i+dy,r.ci_low,r.ci_high,color=color,lw=1);ax.scatter(r.rho,i+dy,color=color,marker=marker,s=24,label={'original':'原PAC网格','70_90':'70–90 Hz网格'}[grid] if i==0 else None)
    ax.axvline(0,color='#777777',ls='--',lw=.7);ax.set(yticks=range(4),yticklabels=[x[-3:] for x in IDS],ylim=(3.7,-.7),xlim=(-.4,.4),xlabel='患者内动作ρ中位数');ax.legend(loc='lower center',bbox_to_anchor=(.45,-.42),frameon=False,fontsize=8);lab(ax,'c  重定心β与PAC差值关联')
    fig.text(.14,.024,'同一事件、通道与PAC；仅增加同尺度基线扣除。范围为同步轮次重抽样。',fontsize=8)
    save(fig,'S5','Figure_S5_baseline_sensitivity',['BASELINE_pooled_channels.csv','BASELINE_patient_action.csv','BASELINE_patient_rho.csv'],'baseline summary offset and stability of direct relationships')


"""Bind the existing approved local figure/table layouts to current numerical outputs."""
from pathlib import Path
import itertools,json,shutil
import numpy as np,pandas as pd
from ncs_method.io import write_json

def bind(display_input,run,out):
 old=Path(display_input);s=out/'SOURCE_DATA';s.mkdir(parents=True,exist_ok=True)
 reuse=[]
 for pat in ['TASK_*tfr.npz','IMAGING_*selected_slices.npz','MANUSCRIPT_case_pairing_coverage_reused.csv','MANUSCRIPT_CST_comparison_reused.csv','MULTIMODAL_*csv','TEMPORAL_*csv.gz','IMAGING_*QC.csv','IMAGING_*verification.csv','IMAGING_*source*.csv','IMAGING_T1*csv']:
  for p in (old/'SOURCE_DATA').glob(pat):
   if p.resolve()!=(s/p.name).resolve():shutil.copyfile(p,s/p.name)
   reuse.append(p.name)
 for p in (run/'tables').glob('*.csv'):shutil.copyfile(p,s/('NCS_'+p.name))
 st=pd.read_csv(run/'tables/hierarchical_statistics.csv');st['comparison']=st.contrast.replace({'comparison_minus_reference':'Imagine_minus_Move'});st['patient_id']=st.subject;st['grid']=st.pac_grid.replace({'full':'original','narrow':'70_90'})
 def save(d,name):d.to_csv(s/name,index=False,float_format='%.17g')
 ch=pd.read_csv(run/'tables/channel_conditions.csv').rename(columns={'subject':'patient_id','beta_original':'beta_db','pac_full':'pac_original','pac_narrow':'pac_70_90','amplitude_power_db':'gamma70_90_db'})
 delta=pd.read_csv(run/'tables/channel_action_differences.csv').rename(columns={'subject':'patient_id','delta_beta_original':'beta_db','delta_beta_same_scale':'beta_same_scale','delta_beta_baseline_level':'beta_baseline_level','delta_pac_full':'pac_original','delta_pac_narrow':'pac_70_90','delta_amplitude_power_db':'gamma70_90_db'});delta['condition']='Imagine_minus_Move'
 save(pd.concat([ch,delta],ignore_index=True),'JOINT_channel_pairs.csv')
 save(ch.rename(columns={'beta_same_scale':'centered_beta_db','beta_baseline_level':'baseline_summary_db','beta_db':'original_task_db'}),'BASELINE_channel_conditions.csv')
 def effects(definition):
  result=[]
  for (pid,act,cond),g in st[st.category=='effect'].groupby(['patient_id','action','comparison'],sort=False):
   row=dict(patient_id=pid,action=act,condition=cond,n_channels=int(g.n_channels.iloc[0]),n_cycles=int(g.n_rounds.iloc[0]),n_complete_cycles=int(g.n_rounds.iloc[0]))
   for m,name in [('beta_'+definition,'beta_db' if definition=='original' else 'centered_beta_db'),('pac_full','pac_original'),('pac_narrow','pac_70_90')]:
    r=g[g.metric==m].iloc[0];row[name]=r.estimate
    pre='beta' if name=='beta_db' else name
    row[pre+'_ci_low']=r.lower;row[pre+'_ci_high']=r.upper
   if definition=='same_scale':row['ci_low']=row.pop('centered_beta_db_ci_low');row['ci_high']=row.pop('centered_beta_db_ci_high')
   result.append(row)
  return pd.DataFrame(result)
 eff=effects('original');save(eff,'JOINT_patient_action_estimates.csv');save(effects('same_scale'),'BASELINE_patient_action.csv')
 for cat,stem in [('association','action'),('subject','patient')]:
  for definition in ['original','same_scale']:
   data=[]
   keys=['patient_id','comparison','grid']+(['action'] if cat=='association' else [])
   for k,g in st[(st.category==cat)&(st.beta_definition==definition)].groupby(keys,sort=False):
    row=dict(zip(keys,k));row.update(n_channels=int(g.n_channels.iloc[0]),n_cycles=int(g.n_rounds.iloc[0]),n_actions=5)
    for m,c in [('rho','rho'),('slope','slope_MI_per_dB'),('partial_rho','partial_rho_control_gamma70_90')]:
     v=g[g.metric==m].iloc[0];row.update({c:v.estimate,c+'_ci_low':v.lower,c+'_ci_high':v.upper})
    data.append(row)
   d=pd.DataFrame(data)
   if definition=='original':save(d,f'JOINT_{stem}_associations.csv')
   else:
    save(d,f'M1_{stem}_full_associations.csv');save(d.rename(columns={'rho_ci_low':'ci_low','rho_ci_high':'ci_high'}),f'BASELINE_{stem}_rho.csv')
 pooled=pd.read_csv(run/'tables/combined_channel_conditions.csv')
 save(pooled.rename(columns={'subject':'patient_id','original':'original_task_db','same_scale':'centered_task_minus_baseline_db','baseline_level':'baseline_summary_db'}),'BASELINE_pooled_channels.csv')
 save(pooled.rename(columns={'subject':'record_id','channel':'channel_slot','original':'task_mean_of_trial_median_db'}),'TASK_all_channel_pooled_beta.csv')
 save(pooled.groupby(['subject','condition'],sort=False)['original'].median().reset_index().rename(columns={'subject':'record_id','original':'median_task_db'}),'TASK_pooled_patient_beta.csv')
 cst=pd.read_csv(run/'tables/structure.csv').rename(columns={'subject':'patient_id','n_voxels':'n_mask_voxels',**{k+'_mean':'mean_'+k.upper() for k in ['fa','md','rd','ad']}});cst['side']=cst.side.str.title();save(cst,'IMAGING_CST_quantitative_reused.csv')
 # Reproduce the prior descriptive 16-sign summary from NEW patient statistics.
 pat=pd.read_csv(s/'JOINT_patient_associations.csv');rows=[]
 signs=np.array(list(itertools.product([-1,1],repeat=4)))
 for (cond,grid),g in pat.groupby(['comparison','grid'],sort=False):
  for m in ['rho','slope_MI_per_dB','partial_rho_control_gamma70_90']:
   v=g[m].to_numpy();mu=v.mean();p=np.mean(abs((signs*v).mean(1))>=abs(mu)-1e-15)
   rows.append(dict(comparison=cond,grid=grid,metric=m,n_patients=4,mean_of_patient_action_medians=mu,min_patient=v.min(),max_patient=v.max(),exact_patient_signflip_two_sided_p=p,inference='descriptive inherited 16-sign summary; no population claim'))
 save(pd.DataFrame(rows),'JOINT_four_patient_summary.csv')
 # Regenerate every formatted supplementary cell using explicit provenance keys.
 template=json.loads((old/'SOURCE_DATA/SUPPLEMENT_tables.json').read_text())
 def form(v,d=3):return f'{v:.{d}f}'.replace('-','−')
 def interval(row,col,pre=None,f=1,d=3):
  pre=pre or col;return form(row[col]*f,d)+'\n['+form(row[pre+'_ci_low']*f,d)+', '+form(row[pre+'_ci_high']*f,d)+']'
 for t in template['tables']:
  for sub in t['subtables']:
   for row,prov in zip(sub['rows'],sub['row_provenance']):
    df=pd.read_csv(s/Path(prov['source_file']).name);sel=np.ones(len(df),bool)
    for k,v in prov['source_key'].items():sel &= df[k].eq(v).to_numpy()
    assert sel.sum()==1;r=df.loc[sel].iloc[0];prov['unrounded_source_values']=r.to_dict();prov['csv_line_1_based_including_header']=int(np.where(sel)[0][0])+2
    if t['table_id']=='S2':row.update(beta=interval(r,'beta_db','beta'),pac=interval(r,'pac_original',f=1e4),pac70=interval(r,'pac_70_90',f=1e4))
    elif t['table_id'] in ['S3','S4']:row.update(rho=interval(r,'rho',d=4),slope=interval(r,'slope_MI_per_dB',f=1e4),partial=interval(r,'partial_rho_control_gamma70_90',d=4))
    else:
     f=1e4 if r.metric=='slope_MI_per_dB' else 1;row.update(mean=form(r.mean_of_patient_action_medians*f,4),range=form(r.min_patient*f,4)+' 至 '+form(r.max_patient*f,4),p=form(r.exact_patient_signflip_two_sided_p,3))
 template['purpose']='all numeric table cells regenerated from this NCS run; previous layouts reused';write_json(s/'SUPPLEMENT_tables.json',template)
 # PAC frequency example is recomputed from the adapted full cell grids.
 private=json.loads((run/'PRIVATE_LOCAL/input_paths.json').read_text());cfg=json.loads((run/'PRIVATE_LOCAL/executed_config.json').read_text());configdir=Path(private[0]['path']).parent
 examples=list((old/'SOURCE_DATA').glob('TASK_*_corrected_PAC_grid.csv'));assert len(examples)==1
 example_name=examples[0].name;parts=examples[0].stem.split('_');source_subject,source_channel=parts[1:3]
 candidates=[item for item in cfg['subjects'] if json.loads((configdir/item['metadata']).read_text())['subject'].endswith(source_subject)];assert len(candidates)==1
 cfgitem=candidates[0];ap=configdir/cfgitem['arrays'];mp=configdir/cfgitem['metadata'];meta=json.loads(mp.read_text());z=np.load(ap)
 delta=z['pac_task_window_median']-z['pac_baseline_window_median'];ci=meta['channels'].index(source_channel);freq=[]
 for condition in cfg['conditions']:
  ix=[i for i,e in enumerate(meta['events']) if e['condition']==condition];m=np.median(delta[ix,ci],axis=0)
  for ai in [0,1]:
   for pi in range(m.shape[1]):freq.append(dict(condition=condition,amplitude_center_hz=np.mean(meta['amplitude_bands_hz'][ai]),phase_center_hz=np.mean(meta['phase_bands_hz'][pi]),corrected_MI=m[ai,pi]))
 save(pd.DataFrame(freq),example_name)
 write_json(out/'RUN_RECORDS/PUBLICATION_BINDING.json',{'numeric_run':str(run),'all_M0_M1_and_CST_tables_from_current_run':True,'fixed_TFR_and_FA_slice_sources_reused':reuse,'no_old_Word_copy':True,'temporal_curves_reused_from_identical_source_arrays':True,'S5_sign_summary':'recomputed deterministic descriptive 16-sign enumeration from current patient estimates; same prior definition'})
 return st

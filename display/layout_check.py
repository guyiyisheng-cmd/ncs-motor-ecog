"""Lightweight layout assertions, unrelated to numerical methods."""
import json
from pathlib import Path
def require_matplotlib_panel_alignment(fig,axes=None,panel_ids=None,row_groups=None,column_groups=None,json_out=None,strict=True,**kwargs):
    fig.canvas.draw()
    aa=list(axes if axes is not None else [a for a in fig.axes if a.get_label()!='<colorbar>'])
    ids=panel_ids or [str(i) for i in range(len(aa))]
    boxes={k:[v*72/fig.dpi for v in a.get_window_extent().bounds] for k,a in zip(ids,aa)}
    failures=[]
    for group in row_groups or []:
        vals=[boxes[k] for k in group['panels']]
        for j in [1,2,3]:
            if max(v[j] for v in vals)-min(v[j] for v in vals)>1.5:failures.append(('row',group['panels'],j))
    for group in column_groups or []:
        vals=[boxes[k] for k in group['panels']]
        for j in [0,2]:
            if max(v[j] for v in vals)-min(v[j] for v in vals)>1.5:failures.append(('column',group['panels'],j))
    result={'boxes_pt':boxes,'tolerance_pt':1.5,'explicit_group_failures':failures,'scope':'Explicit comparable groups only; visual and PDF collision QA remain required.'}
    if json_out:Path(json_out).write_text(json.dumps(result,indent=2))
    if strict and failures:raise AssertionError(failures)

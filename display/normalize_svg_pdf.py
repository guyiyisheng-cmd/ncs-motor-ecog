"""Preserve Cairo SVG geometry while making physical PDF font sizes explicit.
Cairo encodes Tf=1 and puts size into Tm. Only the equivalent text encoding
is normalized; no text, illustration or scientific image is regenerated.
"""
from pathlib import Path
import os
from pypdf import PdfReader,PdfWriter
from pypdf.generic import ContentStream,FloatObject
import shutil,sys
O=Path(os.environ['NCS_DISPLAY_OUT'])
name=sys.argv[1]
p=O/(('FIGURES_SUPPLEMENTARY_EN/' if name.startswith('Figure_S') else 'FIGURES_MAIN_EN/')+name+'.pdf');shutil.copyfile(p,O/('QA/'+name+'_original_Cairo_encoding.pdf'))
r=PdfReader(p);writer=PdfWriter();page=r.pages[0];cs=ContentStream(page.get_contents(),r);out=[];scale=1.;font=None;line=None
for vals,op in cs.operations:
 if op==b'Tm':
  line=[float(v) for v in vals];a,b,c,d,e,f=line
  assert b==0 and c==0 and a>0 and abs(d+a)<1e-6
  scale=a;vals=[FloatObject(v) for v in [1,0,0,-1,e,f]]
 elif op==b'Tf':
  assert float(vals[1])==1.;font=vals[0];vals=[font,FloatObject(scale)]
 elif op==b'Td':
  tx,ty=[float(v) for v in vals];a,b,c,d,e,f=line;line=[a,b,c,d,e+tx*a+ty*c,f+tx*b+ty*d]
  # Separate independent labels that Cairo batches into one PDF text run.
  out.extend([([],b'ET'),([],b'BT'),([FloatObject(v) for v in [1,0,0,-1,line[4],line[5]]],b'Tm'),([font,FloatObject(scale)],b'Tf')]);continue
 elif op in [b'TD',b'T*',b'Tc',b'Tw',b'Tz']:raise ValueError('Unexpected text state; do not approximate')
 out.append((vals,op))
cs.operations=out;page.replace_contents(cs);writer.add_page(page)
t=p.with_suffix('.normalized.pdf')
with t.open('wb') as f:writer.write(f)
t.replace(p)
print('Normalized SVG PDF text encoding; geometry unchanged')

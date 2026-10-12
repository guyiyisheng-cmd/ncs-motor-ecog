"""Separate Cairo label strings without changing glyph advances or illustration paths.
PDF font widths determine advances; original glyph bytes/fonts are preserved.
"""
from pathlib import Path
import os
from pypdf import PdfReader,PdfWriter
from pypdf.generic import ContentStream,FloatObject,ByteStringObject
O=Path(os.environ['NCS_DISPLAY_OUT']);p=O/'FIGURES_MAIN_EN/Figure_1_design.pdf';src=O/'QA/Figure_1_design_original_Cairo_encoding.pdf'
r=PdfReader(src);wr=PdfWriter();wr.add_page(r.pages[0]);page=wr.pages[0];cs=ContentStream(page.get_contents(),wr);fonts=page['/Resources']['/Font'];out=[];font=None;scale=1.;x=y=lx=ly=0.;intext=False
cache={}
def widths(name):
 if name in cache:return cache[name]
 f=fonts[name].get_object();m={};step=1;dw=0.
 if f['/Subtype']=='/Type0':
  step=2;d=f['/DescendantFonts'][0].get_object();dw=float(d.get('/DW',1000));ws=d.get('/W',[]);i=0
  while i<len(ws):
   start=int(ws[i]);v=ws[i+1]
   if isinstance(v,list):
    for j,w in enumerate(v):m[start+j]=float(w)
    i+=2
   else:
    for j in range(start,int(v)+1):m[j]=float(ws[i+2])
    i+=3
 else:
  first=int(f.get('/FirstChar',0))
  for j,w in enumerate(f.get('/Widths',[])):m[first+j]=float(w)
 cache[name]=(step,dw,m);return cache[name]
def show(obj):
 global x
 step,dw,m=widths(font)
 raw=obj if isinstance(obj,bytes) else (obj.encode('utf-16-be') if getattr(obj,'autodetect_utf16',False) else obj.get_original_bytes())
 codes=[int.from_bytes(raw[i:i+step],'big') for i in range(0,len(raw),step)]
 out.extend([([],b'BT'),([FloatObject(v) for v in [1,0,0,-1,x,y]],b'Tm'),([font,FloatObject(scale)],b'Tf'),([ByteStringObject(raw)],b'Tj'),([],b'ET')])
 x+=scale*sum(m.get(c,dw) for c in codes)/1000
for vals,op in cs.operations:
 if op==b'BT':intext=True;continue
 if op==b'ET':intext=False;continue
 if op==b'Tm':
  a,b,c,d,e,f=map(float,vals);assert b==c==0 and a>0 and abs(d+a)<1e-6;scale=a;x=lx=e;y=ly=f
 elif op==b'Tf':font=vals[0];assert float(vals[1])==1
 elif op==b'Td':
  dx,dy=map(float,vals);lx+=dx*scale;ly-=dy*scale;x=lx;y=ly
 elif op==b'Tj':show(vals[0])
 elif op==b'TJ':
  for item in vals[0]:
   if isinstance(item,(str,bytes)):show(item)
   else:x-=float(item)*scale/1000
 elif op in [b'TD',b'T*',b'Tc',b'Tw',b'Tz',b'Tr',b'Ts']:raise ValueError(op)
 else:out.append((vals,op))
cs.operations=out;page.replace_contents(cs)
with p.open('wb') as f:wr.write(f)
print('Preserved source glyphs and advances; explicit physical font sizes; independent text strings.')

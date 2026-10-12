"""Export all rows of a logical table from the authorized, versioned table bundle."""
from pathlib import Path
import argparse,csv,json
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-dir',type=Path,required=True)
 p.add_argument('--table',required=True,choices=['1']+[f'S{i}' for i in range(1,10)]+['all'])
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();data=json.loads((a.input_dir/'TABLES_EN.json').read_text());a.out.mkdir(parents=True,exist_ok=True)
 ids=list(data) if a.table=='all' else [a.table]
 for key in ids:
  for i,block in enumerate(data[key],1):
   path=a.out/f'Table_{key}_part_{i:02d}_EN.csv'
   if path.exists():p.error('Refusing to overwrite '+str(path))
   with path.open('w',newline='',encoding='utf-8') as f:csv.writer(f).writerows(block['rows'])
  (a.out/f'Table_{key}_EN.json').write_text(json.dumps(data[key],ensure_ascii=False,indent=2))
 print('Exported complete supplied tables, without estimating or inferring numerical values.')
if __name__=='__main__':main()

"""Export supplied table cells, not statistical estimates, from minimal table JSON."""
from pathlib import Path
import argparse,csv,json
TABLE_IDS=['1']+[f'S{i}' for i in range(1,10)]

def load_table(root,key):
 # A single approved table takes precedence; do not open an unrelated full bundle.
 single=Path(root)/f'Table_{key}_EN.json'
 if single.is_file():
  data=json.loads(single.read_text())
  return data[key] if isinstance(data,dict) and key in data else data
 bundle=Path(root)/'TABLES_EN.json'
 if not bundle.is_file():raise FileNotFoundError(f'Missing required table input: {single.name} (or legacy TABLES_EN.json containing {key})')
 data=json.loads(bundle.read_text())
 if key not in data:raise ValueError(f'Table {key} is absent from supplied TABLES_EN.json')
 return data[key]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input-dir',type=Path,required=True)
 p.add_argument('--table',required=True,choices=TABLE_IDS+['all'])
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();ids=TABLE_IDS if a.table=='all' else [a.table]
 try:tables={key:load_table(a.input_dir,key) for key in ids}
 except (FileNotFoundError,ValueError) as e:p.error(str(e))
 a.out.mkdir(parents=True,exist_ok=True)
 for key,blocks in tables.items():
  paths=[a.out/f'Table_{key}_part_{i:02d}_EN.csv' for i in range(1,len(blocks)+1)]+[a.out/f'Table_{key}_EN.json']
  for path in paths:
   if path.exists():p.error('Refusing to overwrite '+str(path))
 for key,blocks in tables.items():
  for i,block in enumerate(blocks,1):
   with (a.out/f'Table_{key}_part_{i:02d}_EN.csv').open('w',newline='',encoding='utf-8') as f:csv.writer(f).writerows(block['rows'])
  (a.out/f'Table_{key}_EN.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2))
 print('Exported complete supplied tables, without estimating or inferring numerical values.')
if __name__=='__main__':main()

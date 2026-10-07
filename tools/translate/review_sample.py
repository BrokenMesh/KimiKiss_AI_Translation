# Review aid: print Japanese and English side by side. Usage: review_sample.py SCENE[,SCENE...] N_LINES SEED [regex]
# Without a regex: N_LINES/8 random runs of 8 consecutive lines; with a regex: every line whose English matches.
import sys,json,random,re
sys.path.insert(0,'tools/translate')
import store
scenes=sys.argv[1].split(','); n=int(sys.argv[2]); seed=int(sys.argv[3]) if len(sys.argv)>3 else 1
random.seed(seed)
rows=[]
for sc in scenes:
    recs={r['id']:r for r in json.load(open(f'text/{sc}.json'))}
    f=store.load_scene(f'translation/en/{sc}.txt')
    for e in f.entries:
        if e.tr and e.id in recs: rows.append((e.id,recs[e.id].get('speaker') or '-',recs[e.id]['text'],e.tr))
mode=sys.argv[4] if len(sys.argv)>4 else 'sample'
if mode=='sample':
    # contiguous runs give context: pick n/8 starting points, 8 lines each
    out=[]
    for st in sorted(random.sample(range(len(rows)-8),max(1,n//8))):
        out+=rows[st:st+8]+[None]
else:
    out=[r for r in rows if re.search(mode,r[3])]
for r in out:
    if r is None: print('---'); continue
    print(f'{r[0]} {r[1]}\n  J {r[2]}\n  E {r[3]}')

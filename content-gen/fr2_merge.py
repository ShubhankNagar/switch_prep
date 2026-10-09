import json, os, re, glob, subprocess, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, 'fr2_parts')
OUT = '/home/claude/switch-prep/frontend/public/content/final-round-2.json'
SCR = '/tmp/claude-0/-home-claude/44e2e59b-5817-588f-a4b0-0b7e801c6498/scratchpad/compile'
compile_ = '--compile' in sys.argv
def wc(s): return len(re.sub(r'```.*?```', ' ', s, flags=re.S).split())
days = []
for d in range(8, 15):
    p = os.path.join(PARTS, f'day{d}.json')
    if os.path.exists(p): days.append(json.load(open(p, encoding='utf-8')))
warn = 0
for d in days:
    for m in d['mcqs']:
        w = wc(m['explanation'])
        if not 20 <= w <= 80: print('MCQ expl', m['id'], w); warn += 1
        if len(set(m['options'])) != 4: print('dup opts', m['id'])
    for c in d['coding']:
        w = wc(c['explanation'])
        if not 50 <= w <= 150: print('code expl', c['id'], w); warn += 1
    for t in d['theory']:
        w = wc(t['a'])
        if not 50 <= w <= 150: print('theory', t['id'], w); warn += 1
    ans = [m['answer'] for m in d['mcqs']]
    print('day', d['day'], 'answer dist', [ans.count(i) for i in range(4)])
if compile_:
    shutil.rmtree(SCR, ignore_errors=True)
    for d in days:
        for c in d['coding']:
            dr = os.path.join(SCR, c['id']); os.makedirs(dr)
            open(os.path.join(dr, 'S.java'), 'w').write(c['solution'])
            r = subprocess.run(['javac', '-d', dr, os.path.join(dr, 'S.java')], capture_output=True, text=True)
            err = '\n'.join(l for l in r.stderr.splitlines() if 'JAVA_TOOL' not in l)
            if r.returncode: print('COMPILE FAIL', c['id'], err[:1500])
            else: print('compiled', c['id'])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"days": days}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
x = json.load(open(OUT, encoding='utf-8'))
print('days', len(x['days']), 'mcqs', sum(len(d['mcqs']) for d in x['days']), 'coding', sum(len(d['coding']) for d in x['days']), 'theory', sum(len(d['theory']) for d in x['days']), 'warnings', warn)

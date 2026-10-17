from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/'cases.json').read_text())
assert hashlib.sha256((ROOT/'workflow_cost.py').read_bytes()).hexdigest()==d['source']['workflow_cost_sha256'],'CLI bytes changed'
reports=[]
for c in d['cases']:
 cmd=[sys.executable,'-B',str(ROOT/'workflow_cost.py'),str(ROOT/(c['id']+'.csv')),'--task','Fictional evidence review','--criterion','Fictional reviewer accepts identity and dated source evidence','--currency','USD']
 r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
 report=json.loads(r.stdout)
 for key,value in c['expected'].items():assert report[key]==value,(c['id'],key)
 if report['accepted_results']==0:assert report['cost_per_accepted_result_exact_fraction'] is None
 reports.append({'case':c['id'],'passed':True,'report':report})
# A missing cost cannot silently become the explicit zero used in case3.
with tempfile.TemporaryDirectory() as tmp:
 bad=Path(tmp)/'unknown.csv';bad.write_text((ROOT/'03-known-zero.csv').read_text().replace('A,1,accepted,0,','A,1,accepted,,',1))
 r=subprocess.run([sys.executable,'-B',str(ROOT/'workflow_cost.py'),str(bad),'--task','Fictional','--criterion','Fictional','--currency','USD'],capture_output=True,text=True)
 assert r.returncode==2 and not r.stdout and 'missing is not zero' in r.stderr
print(json.dumps({'cases':reports,'missing_cost_negative_control':'PASS'},indent=2))

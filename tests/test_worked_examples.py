import hashlib,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/'examples/worked-cases'
class WorkedExamples(unittest.TestCase):
    def test_bundled_cli_matches_repository(self):
        self.assertEqual((ROOT/'workflow_cost.py').read_bytes(),(CASES/'workflow_cost.py').read_bytes())
    def test_standalone_cases_and_missing_cost_control(self):
        result=subprocess.run([sys.executable,'-B',str(CASES/'verify_examples.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(len(report['cases']),3)
        self.assertTrue(all(c['passed'] for c in report['cases']))
        self.assertEqual(report['missing_cost_negative_control'],'PASS')
if __name__=='__main__':unittest.main()

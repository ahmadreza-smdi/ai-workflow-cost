import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'workflow_cost.py'
HEADER = 'result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost\n'
GOOD = 'A,1,rejected,0.04,0.01,0.50,0\nA,2,accepted,0.03,0,0.25,0\nB,1,error,0.02,0,0,0\n'


class LedgerBehavior(unittest.TestCase):
    def call(self, data, *extra):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.csv'
            path.write_text(data, encoding='utf-8')
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), str(path), '--task', 'Fictional review', '--criterion', 'Fictional criterion', '--currency', 'USD', *extra], capture_output=True, text=True)
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())
            return result

    def test_retry_and_failed_costs_count_once_per_result(self):
        r = self.call(HEADER + GOOD)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual((d['attempts'], d['results_attempted'], d['accepted_results']), (3, 2, 1))
        self.assertEqual(d['total_cost'], '0.85')
        self.assertEqual(d['cost_per_accepted_result'], '0.850000000')

    def test_no_accepted_result_is_null_not_zero(self):
        d = json.loads(self.call(HEADER + 'A,1,error,1,0,2,0\n').stdout)
        self.assertIsNone(d['cost_per_accepted_result'])
        self.assertEqual(d['total_cost'], '3')
        self.assertEqual(d['accepted_results'], 0)

    def test_explicit_zero_cost_accepted_result(self):
        d = json.loads(self.call(HEADER + 'A,1,accepted,0,0,0,0\n').stdout)
        self.assertEqual(d['cost_per_accepted_result'], '0.000000000')

    def test_nonterminating_ratio_keeps_exact_fraction(self):
        data = HEADER + ''.join(f'{x},1,accepted,0,0,0,0\n' for x in 'AB') + 'C,1,accepted,1,0,0,0\n'
        d = json.loads(self.call(data).stdout)
        self.assertEqual(d['cost_per_accepted_result'], '0.333333333')
        self.assertEqual(d['cost_per_accepted_result_exact_fraction'], {'numerator_cost': '1', 'denominator_results': 3})

    def test_invalid_ledgers_fail_without_partial_report(self):
        invalid = {
            'unknown cost': HEADER + 'A,1,accepted,,0,0,0\n',
            'negative': HEADER + 'A,1,accepted,-1,0,0,0\n',
            'nan': HEADER + 'A,1,accepted,NaN,0,0,0\n',
            'infinity': HEADER + 'A,1,accepted,Infinity,0,0,0\n',
            'exponent': HEADER + 'A,1,accepted,1e2,0,0,0\n',
            'duplicate attempt': HEADER + GOOD + 'B,1,error,0,0,0,0\n',
            'post acceptance': HEADER + GOOD + 'A,3,rejected,0,0,0,0\n',
            'double accepted': HEADER + GOOD + 'A,3,accepted,0,0,0,0\n',
            'extra field': HEADER + 'A,1,accepted,0,0,0,0,extra\n',
            'missing field': HEADER + 'A,1,accepted,0,0,0\n',
            'empty': HEADER,
            'missing id': HEADER + ',1,error,0,0,0,0\n',
            'unknown outcome': HEADER + 'A,1,pending,0,0,0,0\n',
            'duplicate header': HEADER.replace('other_cost','model_cost') + GOOD,
            'large amount': HEADER + 'A,1,accepted,1000000000000,0,0,0\n',
        }
        for name, data in invalid.items():
            with self.subTest(name=name):
                r = self.call(data)
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertEqual(r.stdout, '')
                self.assertIn('Input error:', r.stderr)

    def test_currency_label_and_criterion_required(self):
        for extra in [('--currency', 'usd'), ('--currency', 'USD/EUR'), ('--criterion', ' '), ('--task', '')]:
            with self.subTest(extra=extra):
                self.assertEqual(self.call(HEADER + GOOD, *extra).returncode, 2)

    def test_bom_and_quoted_identifiers(self):
        d = json.loads(self.call('\ufeff' + HEADER + '"A,B",1,accepted,0.1,0.2,0.3,0.4\n').stdout)
        self.assertEqual(d['total_cost'], '1.0')

    def test_same_attempt_label_on_different_results_allowed(self):
        d = json.loads(self.call(HEADER + 'A,1,accepted,1,0,0,0\nB,1,accepted,1,0,0,0\n').stdout)
        self.assertEqual(d['accepted_results'], 2)

    def test_rounding_is_half_up_and_does_not_erase_fraction(self):
        d = json.loads(self.call(HEADER + 'A,1,accepted,0.000000001,0,0,0\nB,1,accepted,0,0,0,0\n').stdout)
        self.assertEqual(d['cost_per_accepted_result'], '0.000000001')
        self.assertEqual(d['cost_per_accepted_result_exact_fraction']['denominator_results'], 2)


if __name__ == '__main__':
    unittest.main()

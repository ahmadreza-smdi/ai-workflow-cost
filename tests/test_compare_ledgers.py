import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = 'result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost\n'
MANUAL = HEADER + ''.join(f'{i},1,accepted,0,0,8,0\n' for i in 'ABC')
AI = HEADER + 'A,1,accepted,1,0,5,0\nB,1,accepted,1.4,0,5,0\nC,1,error,1,0,5,0\n'


class Comparison(unittest.TestCase):
    def run_pair(self, left=MANUAL, right=AI, extra=(), same_path=False):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ('manual.csv', 'ai.csv')]
            for path, data in zip(paths, (left, right)):
                path.write_text(data, encoding='utf-8')
            before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
            command = [sys.executable, '-B', str(ROOT / 'compare_ledgers.py'), str(paths[0]),
                       str(paths[0] if same_path else paths[1]), '--task', 'Fictional paired review',
                       '--criterion', 'Fictional evidence rule', '--currency', 'USD', *extra]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths])
            return result

    def test_syntax_error_identifies_left_or_right_ledger_and_line(self):
        malformed = HEADER + '\n"unfinished\nidentifier'
        for side, label in [('left', 'Manual'), ('right', 'AI')]:
            with self.subTest(side=side):
                result = self.run_pair(**{side: malformed})
                self.assertEqual((result.returncode, result.stdout), (2, ''))
                self.assertIn(f"{label!r} ledger: CSV line 4 (record 1; detected here)", result.stderr)
                self.assertNotIn('workflow-cost-compare-', result.stderr)

    def test_semantic_error_uses_custom_workflow_label(self):
        result = self.run_pair(right=AI.replace('1.4,0,5,0', ',0,5,0'),
                               extra=('--right-label', 'Reviewed assistant'))
        self.assertEqual((result.returncode, result.stdout), (2, ''))
        self.assertIn("'Reviewed assistant' ledger: Record 2: model_cost", result.stderr)

    def test_missing_metadata_does_not_produce_partial_comparison(self):
        result = self.run_pair(extra=('--criterion', ' '))
        self.assertEqual((result.returncode, result.stdout), (2, ''))
        self.assertIn('acceptance criterion', result.stderr)

    def test_lower_total_can_have_higher_unit_cost(self):
        result = self.run_pair()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['shared_results_attempted'], 3)
        left, right = [w['summary'] for w in report['workflows']]
        self.assertEqual((left['total_cost'], left['accepted_results'], left['cost_per_accepted_result']), ('24', 3, '8.000000000'))
        self.assertEqual((right['total_cost'], right['accepted_results'], right['cost_per_accepted_result']), ('18.4', 2, '9.200000000'))
        self.assertNotIn('winner', report)

    def test_retry_cost_is_included(self):
        retry = AI.replace('A,1,accepted,1,0,5,0', 'A,1,rejected,1,0,5,0\nA,2,accepted,1,0,5,0')
        report = json.loads(self.run_pair(right=retry).stdout)
        right = report['workflows'][1]['summary']
        self.assertEqual((right['attempts'], right['accepted_results'], right['total_cost']), (4, 2, '24.4'))

    def test_zero_and_no_acceptances_remain_distinct(self):
        left = HEADER + 'A,1,accepted,0,0,0,0\n'
        right = HEADER + 'A,1,rejected,1,0,0,0\n'
        report = json.loads(self.run_pair(left, right).stdout)
        a, b = [w['summary'] for w in report['workflows']]
        self.assertEqual(a['cost_per_accepted_result'], '0.000000000')
        self.assertIsNone(b['cost_per_accepted_result'])
        self.assertEqual(b['total_cost'], '1')

    def test_unmatched_population_refused_without_partial_output(self):
        for right in (AI.replace('C,1,error', 'D,1,error'), HEADER + AI.splitlines()[1] + '\n'):
            with self.subTest(right=right):
                result = self.run_pair(right=right)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertIn('same result IDs', result.stderr)

    def test_invalid_ledger_refused_without_partial_output(self):
        for right in (AI.replace('1.4,0,5,0', ',0,5,0'), AI + 'A,2,error,0,0,0,0\n', HEADER):
            with self.subTest(right=right):
                result = self.run_pair(right=right)
                self.assertEqual((result.returncode, result.stdout), (2, ''))

    def test_labels_and_same_file_guard(self):
        for extra in (('--right-label', 'manual'), ('--left-label', ' ')):
            self.assertEqual(self.run_pair(extra=extra).returncode, 2)
        self.assertEqual(self.run_pair(same_path=True).returncode, 2)

    def test_hardlinked_names_refused_without_partial_output(self):
        with tempfile.TemporaryDirectory() as folder:
            left = Path(folder) / 'manual.csv'
            right = Path(folder) / 'ai.csv'
            left.write_text(MANUAL, encoding='utf-8')
            try:
                right.hardlink_to(left)
            except OSError as error:
                self.skipTest('Filesystem cannot create this hard-link fixture: ' + str(error))
            self.assertTrue(left.samefile(right))
            before = left.read_bytes()
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT/'compare_ledgers.py'), str(left), str(right),
                 '--task', 'Fictional paired review', '--criterion', 'Fictional rule', '--currency', 'USD'],
                capture_output=True, text=True)
            self.assertEqual((result.returncode, result.stdout), (2, ''))
            self.assertIn('two separate ledger files', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(left.read_bytes(), before)
            self.assertEqual(right.read_bytes(), before)

    def test_equal_bytes_in_separate_files_still_allowed(self):
        result = self.run_pair(MANUAL, MANUAL)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['workflows'][0]['input_sha256'], report['workflows'][1]['input_sha256'])
        self.assertEqual(len(report['workflows']), 2)

    def test_bom_and_different_result_order(self):
        right = '\ufeff' + HEADER + '\n'.join(reversed(AI.splitlines()[1:])) + '\n'
        self.assertEqual(self.run_pair(right=right).returncode, 0)

    def test_maximum_decimal_and_exact_fraction_retained(self):
        data = HEADER + 'A,1,accepted,999999999999.999999999,0,0,0\n'
        report = json.loads(self.run_pair(data, data).stdout)
        self.assertEqual(report['workflows'][0]['summary']['total_cost'], '999999999999.999999999')
        self.assertEqual(report['workflows'][0]['summary']['cost_per_accepted_result_exact_fraction']['denominator_results'], 1)


if __name__ == '__main__':
    unittest.main()

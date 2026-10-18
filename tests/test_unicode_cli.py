"""UTF-8 inputs remain usable when a caller captures an ASCII-only CLI stream."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = 'result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost\n'


class UnicodeCLI(unittest.TestCase):
    def run_cli(self, script, paths, *extra):
        env = dict(os.environ, PYTHONIOENCODING='ascii:strict')
        return subprocess.run(
            [sys.executable, '-B', str(ROOT / script), *map(str, paths),
             '--task', 'بررسی فرضی', '--criterion', 'قاعده فرضی',
             '--currency', 'USD', *extra],
            capture_output=True, env=env,
        )

    def test_unicode_path_ids_and_metadata_keep_totals_and_input_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'گزارش.csv'
            path.write_text(HEADER + 'نتیجه,۱,rejected,0.25,0,0,0\n'
                            + 'نتیجه,۲,accepted,0.75,0,0,0\n', encoding='utf-8')
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = self.run_cli('workflow_cost.py', [path])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, b'')
            report = json.loads(result.stdout.decode('ascii'))
            self.assertEqual(report['task'], 'بررسی فرضی')
            self.assertEqual(report['acceptance_criterion'], 'قاعده فرضی')
            self.assertEqual((report['attempts'], report['results_attempted'],
                              report['accepted_results']), (2, 1, 1))
            self.assertEqual(report['total_cost'], '1.00')
            self.assertEqual(report['cost_per_accepted_result'], '1.000000000')
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_unicode_workflow_label_survives_ascii_error_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ('چپ.csv', 'راست.csv')]
            paths[0].write_text(HEADER + 'A,1,accepted,0,0,0,0\n', encoding='utf-8')
            paths[1].write_text(HEADER + 'A,1,accepted,,0,0,0\n', encoding='utf-8')
            before = [p.read_bytes() for p in paths]
            label = 'هوش مصنوعی'
            result = self.run_cli('compare_ledgers.py', paths, '--right-label', label)
            self.assertEqual((result.returncode, result.stdout), (2, b''))
            error = result.stderr.decode('ascii')
            self.assertIn(label.encode('ascii', 'backslashreplace').decode('ascii'), error)
            self.assertIn('model_cost', error)
            self.assertNotIn('Traceback', error)
            self.assertNotIn('workflow-cost-compare-', error)
            self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_missing_unicode_path_gives_input_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'گزارش.csv'
            result = self.run_cli('workflow_cost.py', [path])
            self.assertEqual((result.returncode, result.stdout), (2, b''))
            error = result.stderr.decode('ascii')
            self.assertIn('Input error:', error)
            self.assertIn(path.name.encode('ascii', 'backslashreplace').decode('ascii'), error)
            self.assertNotIn('Traceback', error)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()

"""Input-path compatibility, including pathlib's pre-3.13 loop exception."""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import compare_ledgers

HEADER = 'result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost\n'


class PathResolution(unittest.TestCase):
    def test_legacy_loop_in_either_input_is_an_input_error(self):
        original_resolve = Path.resolve
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ('left.csv', 'right.csv')]
            for path in paths:
                path.write_text(HEADER + 'A,1,accepted,0,0,0,0\n', encoding='utf-8')
            before = [path.read_bytes() for path in paths]
            for bad in paths:
                with self.subTest(input=bad.name):
                    def legacy_resolve(path, *args, **kwargs):
                        if path == bad:
                            raise RuntimeError('Symlink loop from pre-3.13 pathlib')
                        return original_resolve(path, *args, **kwargs)
                    out, err = io.StringIO(), io.StringIO()
                    argv = ['compare_ledgers.py', *map(str, paths), '--task', 'Fictional task',
                            '--criterion', 'Fictional rule', '--currency', 'USD']
                    with patch.object(Path, 'resolve', legacy_resolve), patch.object(sys, 'argv', argv):
                        with redirect_stdout(out), redirect_stderr(err):
                            code = compare_ledgers.main()
                    self.assertEqual((code, out.getvalue()), (2, ''))
                    self.assertIn('Input error:', err.getvalue())
                    self.assertIn('Cannot resolve ledger path', err.getvalue())
                    self.assertEqual(before, [path.read_bytes() for path in paths])

    def test_real_symlink_loop_is_rejected_without_partial_report(self):
        with tempfile.TemporaryDirectory() as folder:
            loop, other = Path(folder) / 'loop.csv', Path(folder) / 'other.csv'
            try:
                loop.symlink_to(loop.name)
            except (OSError, NotImplementedError) as error:
                self.skipTest('Symlink creation unavailable: ' + str(error))
            other.write_text(HEADER + 'A,1,accepted,0,0,0,0\n', encoding='utf-8')
            before = other.read_bytes()
            run = subprocess.run([sys.executable, '-B', str(ROOT / 'compare_ledgers.py'),
                                  str(loop), str(other), '--task', 'Fictional task',
                                  '--criterion', 'Fictional rule', '--currency', 'USD'],
                                 capture_output=True, text=True)
            self.assertEqual((run.returncode, run.stdout), (2, ''))
            self.assertIn('Input error:', run.stderr)
            self.assertNotIn('Traceback', run.stderr)
            self.assertEqual(loop.readlink(), Path(loop.name))
            self.assertEqual(other.read_bytes(), before)

    def test_unrelated_runtime_error_is_not_reclassified_as_path_error(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ('left.csv', 'right.csv')]
            for path in paths:
                path.write_text(HEADER + 'A,1,accepted,0,0,0,0\n', encoding='utf-8')
            with patch.object(compare_ledgers, 'summarize', side_effect=RuntimeError('unrelated bug')):
                with self.assertRaisesRegex(RuntimeError, 'unrelated bug'):
                    compare_ledgers.compare(*paths, 'Fictional task', 'Fictional rule', 'USD')


if __name__ == '__main__':
    unittest.main()

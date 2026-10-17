import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('paired_builder', ROOT / 'examples/paired-ledgers/build_package.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
ARCHIVE = ROOT / 'examples/AI-Cost-Paired-Ledgers.zip'


class PairedPackage(unittest.TestCase):
    def test_exact_seven_source_members(self):
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.assertEqual(len(archive.namelist()), 7)
            self.assertEqual(set(archive.namelist()), set(builder.FILES))
            self.assertIsNone(archive.testzip())
            for name, source in builder.FILES.items():
                self.assertEqual(archive.read(name), builder.normalized((ROOT / source).read_bytes()), name)

    def test_fresh_extraction_demo_and_eight_packaged_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            with zipfile.ZipFile(ARCHIVE) as archive:
                self.assertEqual(set(archive.namelist()), set(builder.FILES))
                archive.extractall(folder)
            demo = subprocess.run([sys.executable, '-B', 'compare_ledgers.py',
                'examples/paired-ledgers/fictional-manual.csv', 'examples/paired-ledgers/fictional-ai.csv',
                '--task', 'Fictional paired review', '--criterion', 'Fictional evidence rule', '--currency', 'USD'],
                cwd=folder, capture_output=True, text=True)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            reports = [row['summary'] for row in json.loads(demo.stdout)['workflows']]
            self.assertEqual([row['cost_per_accepted_result'] for row in reports], ['8.000000000', '9.200000000'])
            checks = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                    cwd=folder, capture_output=True, text=True)
            self.assertEqual(checks.returncode, 0, checks.stderr)
            self.assertIn('Ran 11 tests', checks.stderr)

    def test_rebuild_logical_contents_match_and_crlf_normalization_is_bounded(self):
        rebuilt, _ = builder.payload()
        with zipfile.ZipFile(io.BytesIO(rebuilt)) as fresh, zipfile.ZipFile(ARCHIVE) as saved:
            self.assertEqual(fresh.namelist(), saved.namelist())
            for name in fresh.namelist():
                self.assertEqual(fresh.read(name), saved.read(name))
        self.assertEqual(builder.normalized(b'row\r\nnext\n'), b'row\nnext\n')
        self.assertNotEqual(builder.normalized(b'changed\r\n'), builder.normalized(b'original\n'))


if __name__ == '__main__':
    unittest.main()

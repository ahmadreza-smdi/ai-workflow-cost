"""Build the seven-file offline companion from captured repository sources."""
import io
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    'index.html': 'examples/paired-ledgers/index.html',
    'workflow_cost.py': 'workflow_cost.py',
    'compare_ledgers.py': 'compare_ledgers.py',
    'examples/paired-ledgers/fictional-manual.csv': 'examples/paired-ledgers/fictional-manual.csv',
    'examples/paired-ledgers/fictional-ai.csv': 'examples/paired-ledgers/fictional-ai.csv',
    'tests/test_compare_ledgers.py': 'tests/test_compare_ledgers.py',
    'LICENSE': 'LICENSE',
}


def normalized(data):
    data.decode('utf-8')
    return data.replace(b'\r\n', b'\n')


def payload():
    raw = {source: (ROOT / source).read_bytes() for source in FILES.values()}
    contents = {name: normalized(raw[source]) for name, source in FILES.items()}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(contents):
            info = zipfile.ZipInfo(name, (2026, 10, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, contents[name])
    with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(FILES) or len(archive.namelist()) != 7:
            raise ValueError('Package structure differs from the seven-file allowlist')
        if any(archive.read(name) != data for name, data in contents.items()):
            raise ValueError('Package contents differ from captured source')
    return stream.getvalue(), raw


def build(output=None):
    output = Path(output) if output is not None else ROOT / 'examples/AI-Cost-Paired-Ledgers.zip'
    data, captured = payload()
    with tempfile.TemporaryDirectory(dir=output.parent) as folder:
        staged = Path(folder) / output.name
        staged.write_bytes(data)
        if any((ROOT / source).read_bytes() != before for source, before in captured.items()):
            raise ValueError('Package source changed; no archive replaced')
        staged.replace(output)
    return output


if __name__ == '__main__':
    print(build())

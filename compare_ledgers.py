"""Compare two private attempt ledgers; acceptance and cost completeness remain caller judgements."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile

from workflow_cost import summarize


def compare(left, right, task, criterion, currency, left_label='Manual', right_label='AI'):
    labels = [left_label.strip(), right_label.strip()]
    if not all(labels) or labels[0].casefold() == labels[1].casefold():
        raise ValueError('Workflow labels must be nonempty and distinct')
    try:
        paths = [Path(left).resolve(), Path(right).resolve()]
    except RuntimeError as error:
        # Python 3.10–3.12 raises RuntimeError for a symlink loop here.
        # Keep the catch local: unrelated calculation errors must still surface.
        raise ValueError('Cannot resolve ledger path: ' + str(error)) from error
    if paths[0] == paths[1]:
        raise ValueError('Use two separate ledger files')
    # Capture each input once: summaries and population checks use the same bytes.
    snapshots = [path.read_bytes() for path in paths]
    reports, populations = [], []
    with tempfile.TemporaryDirectory(prefix='workflow-cost-compare-') as folder:
        for index, data in enumerate(snapshots):
            snapshot = Path(folder) / f'{index}.csv'
            snapshot.write_bytes(data)
            try:
                reports.append(summarize(snapshot, task, criterion, currency))
            except (ValueError, UnicodeError, csv.Error) as error:
                raise ValueError(f'{labels[index]!r} ledger: {error}') from error
            rows = csv.DictReader(io.StringIO(data.decode('utf-8-sig'), newline=''), strict=True)
            populations.append({row['result_id'].strip() for row in rows})
    if populations[0] != populations[1]:
        raise ValueError('Both ledgers must contain exactly the same result IDs; do not silently drop unmatched results')
    return {
        'schema_version': 1,
        'educational_notice': 'Educational, not financial advice.',
        'task': task.strip(), 'acceptance_criterion': criterion.strip(),
        'currency_label': currency, 'shared_results_attempted': len(populations[0]),
        'workflows': [dict(label=label, input_sha256=hashlib.sha256(data).hexdigest(), summary=report)
                      for label, data, report in zip(labels, snapshots, reports)],
        'scope': 'Same recorded result IDs only. Caller must use the same task, period, acceptance rule and cost allocation. No independent quality, completeness, fairness, causal or ROI verification.',
        'interpretation': 'Read total cost, accepted results and cost per accepted result together. Null unit cost means no accepted results, not zero. No workflow winner is selected.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left')
    parser.add_argument('right')
    parser.add_argument('--task', required=True)
    parser.add_argument('--criterion', required=True)
    parser.add_argument('--currency', required=True)
    parser.add_argument('--left-label', default='Manual')
    parser.add_argument('--right-label', default='AI')
    args = parser.parse_args()
    try:
        report = compare(args.left, args.right, args.task, args.criterion,
                         args.currency, args.left_label, args.right_label)
    except (ValueError, OSError, UnicodeError, csv.Error) as error:
        print('Input error: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

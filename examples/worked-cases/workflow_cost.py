"""Offline attempt ledger for Ahmadreza Samadi's cost-per-accepted-result framework."""
import argparse
import csv
from decimal import Decimal, localcontext, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

COSTS = ('model_cost', 'tool_cost', 'review_cost', 'other_cost')
FIELDS = ('result_id', 'attempt_id', 'outcome') + COSTS
AMOUNT = re.compile(r'(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,9})?\Z', re.ASCII)


def _csv_records(stream):
    """Keep DictReader semantics; locate syntax failures by physical input line."""
    physical_line = 0
    completed_records = 0

    def counted_lines():
        nonlocal physical_line
        for line in stream:
            physical_line += 1
            yield line

    rows = csv.DictReader(counted_lines(), strict=True)
    location = 'header'
    try:
        if rows.fieldnames is None or len(rows.fieldnames) != len(FIELDS) or set(rows.fieldnames) != set(FIELDS):
            raise ValueError('CSV requires exactly these unique columns: ' + ','.join(FIELDS))
        location = 'record 1'
        for row in rows:
            completed_records += 1
            yield completed_records, row
            location = f'record {completed_records + 1}'
    except csv.Error as error:
        raise csv.Error(f'CSV line {physical_line} ({location}; detected here): {error}') from error


def summarize(path, task, criterion, currency):
    if not task.strip() or not criterion.strip():
        raise ValueError('Task and acceptance criterion must be explicit and nonempty')
    if not re.fullmatch(r'[A-Z]{3}', currency, flags=re.ASCII):
        raise ValueError('Currency must be a single three-letter uppercase label')
    totals = {key: Decimal(0) for key in COSTS}
    attempts = set()
    results = set()
    accepted = set()
    counts = {'accepted': 0, 'rejected': 0, 'error': 0}
    with localcontext() as context:
        context.prec = 40
        with Path(path).open(newline='', encoding='utf-8-sig') as stream:
            for index, row in _csv_records(stream):
                if index > 100000:
                    raise ValueError('Maximum supported ledger size is 100000 attempts')
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f'Record {index}: wrong field count')
                result, attempt, outcome = (row[key].strip() for key in FIELDS[:3])
                if not result or not attempt or outcome not in counts:
                    raise ValueError(f'Record {index}: IDs required; outcome must be accepted, rejected or error')
                if (result, attempt) in attempts:
                    raise ValueError(f'Record {index}: duplicate result/attempt pair')
                if result in accepted:
                    raise ValueError(f'Record {index}: accepted result is terminal; no subsequent attempts allowed')
                for key in COSTS:
                    amount = row[key].strip()
                    if not AMOUNT.fullmatch(amount):
                        raise ValueError(f'Record {index}: {key} requires explicit nonnegative plain decimal; missing is not zero')
                    totals[key] += Decimal(amount)
                attempts.add((result, attempt))
                results.add(result)
                counts[outcome] += 1
                if outcome == 'accepted':
                    accepted.add(result)
        if not attempts:
            raise ValueError('Ledger has no attempts; cannot summarize an empty experiment')
        total = sum(totals.values(), Decimal(0))
        rate = None if not accepted else format((total / len(accepted)).quantize(Decimal('0.000000001'), rounding=ROUND_HALF_UP), 'f')
        return {
            'schema_version': 1, 'task': task.strip(), 'acceptance_criterion': criterion.strip(),
            'currency_label': currency, 'attempts': len(attempts), 'results_attempted': len(results),
            'accepted_results': len(accepted), 'outcomes': counts,
            'costs': {key: format(value, 'f') for key, value in totals.items()},
            'total_cost': format(total, 'f'), 'cost_per_accepted_result': rate,
            'cost_per_accepted_result_exact_fraction': None if not accepted else {'numerator_cost': format(total, 'f'), 'denominator_results': len(accepted)},
            'undefined_reason': 'No accepted results' if not accepted else None,
            'rounding': 'Displayed unit cost rounds half up to 9 decimal places; exact numerator/denominator retained',
            'scope': 'Caller-recorded costs and acceptance labels only; no independent verification, quality score or currency conversion',
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger')
    parser.add_argument('--task', required=True)
    parser.add_argument('--criterion', required=True)
    parser.add_argument('--currency', required=True)
    args = parser.parse_args()
    try:
        report = summarize(args.ledger, args.task, args.criterion, args.currency)
    except (ValueError, OSError, UnicodeError, csv.Error) as error:
        print('Input error: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

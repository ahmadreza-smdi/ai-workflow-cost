# When the ledger rejects an input

An input error means the CLI could not produce a summary under its input rules. It does not mean the workflow failed, cost nothing or produced no accepted results. Keep your original records and work on a copy.

## The CSV has broken quoting

The current-source CLI identifies the physical line where a CSV syntax error was detected and the logical record being read (or `header`). For example, this **fictional invalid file** has an unclosed quote:

```csv
result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost
A,1,accepted,0,0,0,0

"unfinished
identifier
```

It exits with code `2`, writes no JSON report, and reports:

```text
Input error: CSV line 5 (record 2; detected here): unexpected end of data
```

Physical lines include the header, blank lines and newlines inside quoted fields. Records count parsed nonblank data rows. The detection line is not necessarily where the bad quote began: inspect the preceding record and opening quote too. Properly quoted identifiers may contain commas or newlines; do not remove valid data just to eliminate an error.

Work on a copy and reconcile the CSV export with its source. Restore missing quoting or export it again using a CSV-aware application. A repaired file still needs complete costs, unique attempt pairs and supported outcome labels.

In a two-ledger comparison, the error also identifies the workflow label, for example `'AI' ledger: CSV line 5 ...`. Custom `--left-label` and `--right-label` values identify those workflows. This does not select a winning workflow or validate the records. Older tagged downloads may show less detailed errors; this description applies to the source version containing the diagnostic update.

## A required cost is blank

The four required cost columns are `model_cost`, `tool_cost`, `review_cost` and `other_cost`. A blank value is unknown; the CLI does not substitute zero.

Find the amount and its allocation basis in your records before calculating. Enter `0` only when the cost is known to be zero. If a required cost remains unresolved, keep the experiment unresolved instead of inventing a value.

For example, this **fictional invalid row** is missing its model cost:

```csv
result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost
fictional-a,try-1,accepted,,0,0,0
```

It returns an input error naming `model_cost` and exits with code `2`.

## A result/attempt pair is duplicated

`result_id` groups attempts toward the same result. `attempt_id` distinguishes attempts within that result; the pair must be unique.

Check whether the source contains one attempt copied twice or two actual attempts. Remove a copied row only after reconciling it against the source. Give two real attempts distinct IDs and retain both costs. Do not rename a duplicated row merely to make it pass: that can double-count a single attempt.

This **fictional invalid ledger** repeats the same pair:

```csv
result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost
fictional-a,try-1,rejected,1,0,0,0
fictional-a,try-1,rejected,1,0,0,0
```

It returns `Record 2: duplicate result/attempt pair` and exits with code `2`.

## An accepted result has later attempts

For this CLI, `accepted` is terminal within each result. The input preserves execution order within that result. A later row for it is rejected even when its attempt ID differs.

Reconcile the recorded sequence and outcome labels against your stated acceptance criterion. If an earlier acceptance was provisional, correct the label only when the underlying records support that correction. A changed task or acceptance rule belongs in a separately documented experiment. Do not delete real retries or their costs to force the ledger to pass.

This **fictional invalid sequence** continues after acceptance:

```csv
result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost
fictional-a,try-1,accepted,1,0,0,0
fictional-a,try-2,error,1,0,0,0
```

It returns `Record 2: accepted result is terminal; no subsequent attempts allowed` and exits with code `2`.

## The comparison has unmatched result IDs

The optional `compare_ledgers.py` companion requires exactly the same recorded result IDs in its two separate CSVs. A left file containing only `fictional-a` and a right file containing only `fictional-b` fail with:

```text
Input error: Both ledgers must contain exactly the same result IDs; do not silently drop unmatched results
```

The command exits with code `2` and produces no partial JSON report. Check the source exports, spelling, missing records and intended population. Do not delete unmatched results to force agreement or invent a zero-cost attempt for a result that was never attempted. If the recorded populations truly differ, this helper cannot produce a same-ID comparison from those inputs.

The two ledgers may record different outcomes for the same result ID. For example, one can record `fictional-a` as accepted and the other as error; that outcome difference alone is allowed. A valid ledger with no accepted results still has undefined unit cost (`null`), not zero. Matching IDs alone does not establish the same task, period, acceptance rule, cost allocation, quality or fairness. See the [paired-ledger example](../README.md#compare-two-ledgers-for-the-same-recorded-results).

## A valid summary has no accepted results

This is different from an input error. A valid ledger containing rejected or error attempts can return exit code `0`, retain its recorded total cost and report `cost_per_accepted_result: null` with `undefined_reason: "No accepted results"`.

Do not read `null` as zero unit cost. Conversely, explicitly known zero costs with an accepted result can produce zero unit cost. The [three-state diagram](cost-states.svg) and [worked cases](../examples/worked-cases/) illustrate these separate conditions.

The CLI checks recorded structure and totals. A successful run does not verify acceptance judgements, complete cost capture, experimental fairness or company outcomes. All rows above are fictional teaching examples. Documentation prepared with AI assistance.

[Back to the input contract and run command](../README.md)

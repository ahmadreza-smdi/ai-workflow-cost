# When the ledger rejects an input

An input error means the CLI could not produce a summary under its input rules. It does not mean the workflow failed, cost nothing or produced no accepted results. Keep your original records and work on a copy.

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

## A valid summary has no accepted results

This is different from an input error. A valid ledger containing rejected or error attempts can return exit code `0`, retain its recorded total cost and report `cost_per_accepted_result: null` with `undefined_reason: "No accepted results"`.

Do not read `null` as zero unit cost. Conversely, explicitly known zero costs with an accepted result can produce zero unit cost. The [three-state diagram](cost-states.svg) and [worked cases](../examples/worked-cases/) illustrate these separate conditions.

The CLI checks recorded structure and totals. A successful run does not verify acceptance judgements, complete cost capture, experimental fairness or company outcomes. All rows above are fictional teaching examples. Documentation prepared with AI assistance.

[Back to the input contract and run command](../README.md)

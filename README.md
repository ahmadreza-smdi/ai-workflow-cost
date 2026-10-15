# AI workflow cost ledger

An offline, dependency-free Python CLI by [Ahmadreza Samadi](https://a-samadi.com/about.html), accompanying [AI cost per verified result](https://a-samadi.com/writing/ai-cost-per-verified-result.html).

Count what the whole attempt costs, then divide by distinct results accepted under a stated criterion. Retries and failed attempts still cost money. This utility totals your ledger; it does not decide whether a result is correct.

## Try the fictional example

Python 3.10 or newer; no install, account, API key or network connection required.

```sh
python3 workflow_cost.py examples/fictional-attempts.csv --task "Fictional property-record review" --criterion "Fictional reviewer accepts supported identity and dated evidence" --currency USD
python3 -B -m unittest discover -s tests -v
```

The invented fixture has **3 attempts across 2 results, 1 accepted result and 0.85 total cost** in the selected currency label. The cost per accepted result is 0.85. These are teaching numbers, not Appraiva measurements, customer results or a model benchmark.

## Prepare your ledger

One row per attempt, in execution order within each result. Exact unique headers, in any order:

```text
result_id,attempt_id,outcome,model_cost,tool_cost,review_cost,other_cost
```

- `result_id`: one intended deliverable; keep it stable across retries. A repeated document or candidate must not become a new accepted result merely because it was retried.
- `attempt_id`: unique within its result. Different results may reuse an attempt label.
- `outcome`: `accepted`, `rejected` or `error`. An accepted row closes that result; later attempts for it are rejected as ambiguous input. Split genuinely different deliverables into different result IDs.
- All four cost columns are mandatory. Enter an explicit zero when a category is known to be zero; missing values cause failure. Use nonnegative plain decimals with at most 12 integer and 9 fractional digits. No exponent notation, thousands separators, currency symbols, NaN, infinity, rebates or negative costs. Allocate credits separately before preparing a consistent ledger.
- Price review time yourself using a stated rate and time basis; the utility invents neither wages nor effort. Put other consistently allocated experiment costs in `other_cost`. Do not count the same provider charge, tool bill or review allocation in two rows/categories.

Only combine one currency and one task/acceptance criterion in a run. `--currency` is a three-uppercase-letter **label**, not ISO validation or exchange-rate conversion. The CSV has no currency column; the caller must enforce this input contract. Use separate ledgers for workflows you want to compare. Include their failed and rejected attempts consistently and use the same population, period, acceptance rule and cost categories.

## Interpret the JSON

The numerator sums all four cost categories across every attempt. The denominator counts distinct accepted result IDs. If none is accepted, `cost_per_accepted_result` and its exact fraction are JSON `null`; total spend and zero accepted outputs remain visible. This differs from an explicitly zero-cost accepted result, whose unit cost is zero.

Amounts are decimal strings, not binary floats. Displayed unit cost rounds half up to nine decimal places; the exact numerator and denominator are also retained. Maximum 100,000 attempts per file. Empty ledgers, duplicate headers/attempts, malformed rows, unknown costs and attempts after acceptance fail with exit code 2 and no partial JSON. Successful summaries exit 0, including a run with zero accepted outputs. Usage errors go to stderr. Input bytes are not changed and output goes only to stdout/stderr.

## Limits

Acceptance is a caller-supplied label, not independent verification. This tool does not calculate precision, recall, time to decision, completeness of your cost allocation or product usefulness. Read those measures alongside cost. It cannot establish return on investment, actual property value, a company outcome or which model to buy. Pending decisions must be resolved or excluded under an explicitly documented cutoff before a final run; arbitrary exclusion can bias the comparison. No telemetry or automatic uploads.

Developed with AI assistance and synthetic CLI tests. No performed customer evaluation or independent review is claimed. Original utility code, documentation and fictional fixtures are [MIT licensed](LICENSE); this does not relicense the personal website or its other assets.

# Use the experiment workbook without Python

By [Ahmadreza Samadi](https://a-samadi.com/about.html). This guide describes the existing [v0.1.1 Excel workbook](https://github.com/ahmadreza-smdi/ai-workflow-cost/releases/download/v0.1.1/AI-Workflow-Experiment.xlsx). Its sample records, rates and costs are fictional.

## 1. Save a private copy and define the comparison

Download the workbook and save your working copy privately. Keep customer records and private notes out of this public repository and publicly shared files.

On `Compare`, replace these amber inputs:

| Cell | What to enter |
| --- | --- |
| `B5` | One task definition |
| `B6` | The acceptance rule used for both workflows |
| `B7` | The shared batch or population |
| `B8` | The period and decision cutoff |
| `B9` | One currency label for all amounts |
| `B12`, `C12` | Your stated hourly labor rates for Manual and AI respectively |

Keep the fixed `Manual` and `AI` headings in `B11` and `C11`. They select the matching attempt rows. A currency label performs no exchange-rate conversion.

## 2. Replace the fictional records, preserving formulas

In your private copy, clear **contents only** from `Results!A7:F16` and `Attempts!A7:G36` before entering your own batch. Do not delete worksheet rows or clear whole sheets. Keep the headers, formatting and formula cells.

The labelled capacity is **10 paired results and 30 attempts**. Entries below row 16 on `Results` or row 36 on `Attempts` are outside the summary formulas. Do not extend the apparent batch by typing below those limits.

On `Results`, use one row per intended deliverable:

| Columns | What to enter |
| --- | --- |
| `A` | A unique result ID, shared by both workflows |
| `B`, `C` | Manual and AI final outcomes: `accepted`, `rejected`, `error` or `pending` |
| `D`, `E` | Manual and AI elapsed minutes from starting that result to its final disposition, including waiting |
| `F` | Evidence or reviewer note |
| `G` | Formula status: inspect it, do not overwrite it |

Leave final elapsed time blank for a pending outcome. An `accepted` label records your decision under the stated rule. It does not independently prove correctness.

On `Attempts`, record every attempt, including retries and failures:

| Columns | What to enter |
| --- | --- |
| `A` | Exactly `Manual` or `AI` |
| `B` | A result ID already listed on `Results` |
| `C` | An attempt ID unique within that workflow and result |
| `D`, `E`, `F` | Model cost, tool cost and other **non-labor** cost |
| `G` | Labor minutes, including drafting, review, corrections and handoffs |
| `H:K` | Formulas for hourly rate, labor cost, full cost and input status; do not overwrite |

Enter explicit numeric zero where a cost or labor amount is known to be zero. A missing amount is unknown. Labor cost is calculated from minutes and the rate on `Compare`; do not record the same labor again under other cost.

## 3. Read the result alongside its denominator

The unchanged fictional batch illustrates why a lower total is not enough:

| `Compare` cells | Manual, column B | AI, column C |
| --- | --- | --- |
| Row 16: accepted results | 3 | 2 |
| Row 20: recorded full cost | 24.00 | 18.40 |
| Row 21: cost per accepted result | 24 / 3 = 8.00 | 18.40 / 2 = 9.20 |

Also read intended results on row 15, pending results on row 17 and accepted share on row 18. The example is arithmetic, not measured company performance or a recommendation to choose either workflow.

Row 23 totals labor effort. Row 24 sums per-result elapsed minutes. That sum is not the calendar duration of a parallel batch.

If totals are unavailable, inspect `Results!G7:G16`, `Attempts!K7:K36` and `Compare!B14:C14`. Reconcile missing amounts, invalid numbers, unmatched IDs or duplicates from your records. Do not replace an unknown amount with zero merely to clear a warning. Zero accepted results gives undefined cost per accepted result (`n.a.`).

`Compare!B26` describes recorded comparison readiness. “Recorded batch complete” does not certify a fair experiment, causal improvement or useful output.

## Spreadsheet execution limits

Formula definitions and saved values were checked during the workbook release, with synthetic input-change checks. Native Excel desktop and Google Sheets recalculation remain unverified. In a disposable private copy, check that changing an input updates the related outputs in your spreadsheet application before relying on an edited result. A saved value alone is not evidence of recalculation.

The workbook and CLI have different input layouts. The workbook has labor minutes, rates and pending outcomes; the CLI CSV has four explicit cost columns and accepts only `accepted`, `rejected` and `error`. Do not rename an Excel export to CSV and assume it satisfies the CLI contract. Use the [CLI field rules](../README.md#prepare-your-cli-ledger) when preparing that separate ledger.

Developed with AI assistance. This guide changes no workbook formulas or example records. Read the [method article](https://a-samadi.com/writing/ai-cost-per-verified-result.html) and [AI and property hub](https://a-samadi.com/topics/ai-real-estate.html) for context.

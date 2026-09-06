# AI Finance Controller (Track 04)

An autonomous 3-way multi-source reconciliation, cash position engine, and tax-line classifier with verification-first exception routing.

## Demo Video
- **Walkthrough Pitch (YouTube):** [Watch the 3-Minute Demo](https://youtu.be/kWnVm3CvZjM)

## Loop Closed
1. **Multi-Source Ingestion:** Ingests unlinked raw files (`bank_statement.csv`, `internal_ledger.csv`, `invoices.csv`).
2. **Reconciliation Engine:** Resolves date shifts, fee deductions, and vendor aliases with zero false positives.
3. **Canonical Ledger & Tax Classifier:** Groups records into unified transactions and maps standard corporate tax lines.
4. **Audit & Exception Report:** Exports `data/canonical_ledger.csv` and `data/honest_exception_report.csv` alongside cash position metrics.

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the complete autonomous agent loop
python -m app.main

# Run independent benchmark evaluation
python -m app.evaluator

# Generate aggregate throughput and exception audit
python -m app.generate_report
```

## Evaluator Performance
* **Bank -> Ledger Match Precision:** 100.00% (28/28 true pairs found, 0 FP)
* **Bank -> Invoice Match Precision:** 100.00% (31/31 true pairs found, 0 FP)
* **Tax Line Accuracy:** 87.36%
* **False Positive Rate:** 0.00%
* **Throughput:** >17,000 records/second

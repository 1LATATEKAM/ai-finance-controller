# Track 04 - AI Finance Controller: synthetic dataset

A 79-transaction synthetic batch across three sources, with a hidden ground-truth
key for scoring. Built for the "Multi-source reconciliation + Tax-line matcher"
direction.

## Files
- `bank_statement.csv` - what the bank posted (bank_ref, date, signed amount, short description)
- `internal_ledger.csv` - GL journal entries (journal_id, date, account_code, debit/credit, amount, description)
- `invoices.csv` - vendor invoices (invoice_number, vendor, issue_date, due_date, amount, description)
- `ground_truth.csv` - THE SCORING KEY. Do not feed this to the agent. Maps every
  source record to its true transaction, tax line, and cross-source counterparts.

## Schema notes
- Bank amounts are signed: negative = outflow, positive = inflow.
- Ledger uses debit/credit (DR for expenses, CR for revenue) with GL account codes.
- Invoice amounts are unsigned (invoice totals).
- Every row in every source belongs to exactly one true transaction in ground_truth.
- `presence` = which sources contain the transaction (B/L/I/BLI...).
- `complication` = what makes it hard to match: clean, amount_mismatch, date_shift,
  description_variance, near_duplicate.
- `dup_group` = non-empty for near-duplicate pairs (same vendor, similar amount,
  nearby date) that are easy to confuse.


## Scoring (suggested)
- Match rate: fraction of source records whose true counterpart linkage (txn_id)
  the agent found correctly.
- Tax-line accuracy: fraction of records assigned the correct tax_line.
- Exception rate: fraction of records the agent flagged as unresolved.
- Throughput: records processed per unit time or per call.

The ground truth lets you measure all of these exactly. Aim to report match rate,
tax-line accuracy, and an honest exception list broken down by why each record
failed.

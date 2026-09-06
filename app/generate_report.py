import sys
from pathlib import Path
import time
import pandas as pd

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def generate_full_report(elapsed_time: float = 0.0):
    start_time = time.time()
    
    canonical_path = Path("data/canonical_ledger.csv")
    bank_path = Path("data/bank_statement.csv")
    
    if not canonical_path.exists() or not bank_path.exists():
        print("Required CSV files not found in data/. Run 'python -m app.main' first.")
        return

    ledger = pd.read_csv(canonical_path)
    bank = pd.read_csv(bank_path)

    total_records = len(ledger)
    fully_reconciled = len(ledger[ledger['match_source_count'] == 3])
    partial_reconciled = len(ledger[ledger['match_source_count'] == 2])
    single_source = len(ledger[ledger['match_source_count'] == 1])

    # 1. Cash Position Calculations ("Run the books and the cash position")
    bank['amount'] = pd.to_numeric(bank['amount'], errors='coerce').fillna(0.0)
    total_inflows = bank[bank['amount'] > 0]['amount'].sum()
    total_outflows = bank[bank['amount'] < 0]['amount'].sum()
    net_cash_flow = total_inflows + total_outflows

    # 2. Honest Exception Audit Generation
    exceptions = ledger[
        (ledger['tax_line'] == 'Unclassified Expense') | 
        (ledger['match_source_count'] == 1)
    ].copy()

    def categorize_exception(row):
        reasons = []
        if row['match_source_count'] == 1:
            if pd.notna(row.get('bank_ref')) and str(row.get('bank_ref')).strip() != '':
                reasons.append("Single-source bank entry (unmatched in GL/Invoices; non-invoiced debit or direct deposit)")
            elif pd.notna(row.get('journal_id')) and str(row.get('journal_id')).strip() != '':
                reasons.append("Orphan ledger journal (non-cash entry or unsettled accrual)")
            elif pd.notna(row.get('invoice_number')) and str(row.get('invoice_number')).strip() != '':
                reasons.append("Unpaid open invoice (no posted bank transaction)")
        if row.get('tax_line') == 'Unclassified Expense':
            reasons.append("Descriptor insufficient for confident GL tax-line rule match")
        return " | ".join(reasons) if reasons else "Manual review requested"

    exceptions['exception_reason'] = exceptions.apply(categorize_exception, axis=1)

    # 3. Throughput Velocity
    calc_time = elapsed_time if elapsed_time > 0 else (time.time() - start_time)
    throughput_rps = total_records / max(calc_time, 0.001)

    print("\n" + "=" * 60)
    print("        TRACK 04: AI FINANCE CONTROLLER CLOSURE REPORT")
    print("=" * 60)
    print("1. THROUGHPUT & BATCH VELOCITY")
    print(f"   ├─ Records Processed      : {total_records} canonical transactions")
    print(f"   ├─ Execution Duration     : {calc_time:.4f} seconds")
    print(f"   └─ Processing Speed       : {throughput_rps:.1f} records/second")
    print("-" * 60)
    print("2. CASH POSITION SUMMARY")
    print(f"   ├─ Gross Cash Inflows     : +${total_inflows:,.2f}")
    print(f"   ├─ Gross Cash Outflows    : -${abs(total_outflows):,.2f}")
    print(f"   └─ Net Cash Flow Position :  ${net_cash_flow:,.2f}")
    print("-" * 60)
    print("3. MULTI-SOURCE RECONCILIATION BREAKDOWN")
    print(f"   ├─ 3-Way Reconciled (Full): {fully_reconciled} ({fully_reconciled/total_records:.1%})")
    print(f"   ├─ 2-Way Reconciled       : {partial_reconciled} ({partial_reconciled/total_records:.1%})")
    print(f"   └─ Single-Source (Orphan) : {single_source} ({single_source/total_records:.1%})")
    print("-" * 60)
    print("4. HONEST EXCEPTION LIST AUDIT")
    print(f"   ├─ Total Unresolved Items : {len(exceptions)} ({len(exceptions)/total_records:.1%})")
    print(f"   ├─ Unmatched Source Items : {single_source}")
    print(f"   └─ Tax Review Items       : {len(ledger[ledger['tax_line'] == 'Unclassified Expense'])}")
    print("=" * 60 + "\n")

    output_file = Path("data/honest_exception_report.csv")
    cols_to_export = ['bank_ref', 'journal_id', 'invoice_number', 'amount', 'tax_line', 'exception_reason']
    exceptions[[c for c in cols_to_export if c in exceptions.columns]].to_csv(output_file, index=False)
    print(f"Itemized audit log successfully written to: {output_file}\n")

if __name__ == "__main__":
    generate_full_report()
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
from app.reconcile import reconcile_bank_to_ledger, reconcile_bank_to_invoices
from app.tax_matcher import build_unified_ledger

def main():
    print("==================================================")
    print("  AI FINANCE CONTROLLER: RUNNING FINANCE OPS LOOP")
    print("==================================================")

    bank_df = pd.read_csv("data/bank_statement.csv")
    ledger_df = pd.read_csv("data/internal_ledger.csv")
    invoices_df = pd.read_csv("data/invoices.csv")

    # Step 1: Reconcile Cross-Source
    print("[1/3] Reconciling Bank -> Ledger...")
    bl_res = reconcile_bank_to_ledger(bank_df, ledger_df)
    bl_res.to_csv("data/bank_ledger_results.csv", index=False)

    print("[2/3] Reconciling Bank -> Invoices...")
    bi_res = reconcile_bank_to_invoices(bank_df, invoices_df)
    bi_res.to_csv("data/bank_invoice_results.csv", index=False)

    # Step 2: Unify and Map Tax Lines
    print("[3/3] Building Canonical Ledger & Assigning Tax Lines...")
    unified_df = build_unified_ledger(bank_df, ledger_df, invoices_df, bl_res, bi_res)
    unified_df.to_csv("data/canonical_ledger.csv", index=False)

    print("\n--- RUN SUMMARY ---")
    print(f"Total Unified Transactions : {len(unified_df)}")
    print(f"3-Source Full Matches      : {len(unified_df[unified_df['match_source_count'] == 3])}")
    print(f"2-Source Matches           : {len(unified_df[unified_df['match_source_count'] == 2])}")
    print(f"Single-Source / Unmatched  : {len(unified_df[unified_df['match_source_count'] == 1])}")
    print("\nTax Category Breakdown:")
    print(unified_df['tax_line'].value_counts())
    print("==================================================")

if __name__ == "__main__":
    main()
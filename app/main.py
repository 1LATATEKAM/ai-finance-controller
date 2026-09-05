import pandas as pd

from reconcile import (
    match_bank_to_ledger,
    match_bank_to_invoice
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

BANK_FILE = "data/bank_statement.csv"
LEDGER_FILE = "data/internal_ledger.csv"
INVOICE_FILE = "data/invoices.csv"


bank_df = pd.read_csv(BANK_FILE)
ledger_df = pd.read_csv(LEDGER_FILE)
invoice_df = pd.read_csv(INVOICE_FILE)


print("\n====================================")
print("AI FINANCE CONTROLLER")
print("====================================")

print(f"\nBank records:    {len(bank_df)}")
print(f"Ledger records:  {len(ledger_df)}")
print(f"Invoice records: {len(invoice_df)}")


# ---------------------------------------------------------
# BANK → LEDGER
# ---------------------------------------------------------

print("\n------------------------------------")
print("BANK → LEDGER RECONCILIATION")
print("------------------------------------")

ledger_results = match_bank_to_ledger(
    bank_df,
    ledger_df
)

ledger_results.to_csv(
    "data/bank_ledger_results.csv",
    index=False
)


# ---------------------------------------------------------
# BANK → INVOICE
# ---------------------------------------------------------

print("\n------------------------------------")
print("BANK → INVOICE RECONCILIATION")
print("------------------------------------")

invoice_results = match_bank_to_invoice(
    bank_df,
    invoice_df
)

invoice_results.to_csv(
    "data/bank_invoice_results.csv",
    index=False
)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

print("\n====================================")
print("RECONCILIATION SUMMARY")
print("====================================")

print("\nBank → Ledger:")
print(
    ledger_results["status"]
    .value_counts()
)


print("\nBank → Invoice:")
print(
    invoice_results["status"]
    .value_counts()
)


print("\nAverage Bank → Ledger confidence:",
      round(ledger_results["confidence"].mean(), 3))

print("Average Bank → Invoice confidence:",
      round(invoice_results["confidence"].mean(), 3))


print("\nResults saved:")
print("→ data/bank_ledger_results.csv")
print("→ data/bank_invoice_results.csv")
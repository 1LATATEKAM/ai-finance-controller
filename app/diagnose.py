import pandas as pd

gt = pd.read_csv("data/ground_truth.csv")
bi = pd.read_csv("data/bank_invoice_results.csv")

paired_gt = gt.dropna(subset=['bank_ref', 'invoice_number'])

merged = pd.merge(
    bi, 
    paired_gt[['bank_ref', 'invoice_number', 'complication', 'tax_line']], 
    on='bank_ref', 
    suffixes=('_pred', '_gt')
)

missed = merged[merged['status'] != 'MATCHED']

print(f"\n--- MISSED BANK -> INVOICE MATCHES ({len(missed)} records) ---")
print(missed[['bank_ref', 'invoice_number_gt', 'status', 'complication']].to_string(index=False))
print("\nComplication breakdown among misses:")
print(missed['complication'].value_counts())

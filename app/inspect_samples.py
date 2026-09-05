import pandas as pd

bank = pd.read_csv("data/bank_statement.csv")
inv = pd.read_csv("data/invoices.csv")
gt = pd.read_csv("data/ground_truth.csv")

samples = ['BANK-0001', 'BANK-0009', 'BANK-0015', 'BANK-0004']

for b_ref in samples:
    b_row = bank[bank['bank_ref'] == b_ref].iloc[0]
    row_gt = gt[gt['bank_ref'] == b_ref].iloc[0]
    inv_num = row_gt['invoice_number']
    i_row = inv[inv['invoice_number'] == inv_num].iloc[0] if pd.notna(inv_num) else None
    
    print(f"\n==================== {b_ref} ({row_gt['complication']}) ====================")
    print(f"BANK   : Date={b_row['date']} | Amt={b_row['amount']} | Desc='{b_row['description']}'")
    if i_row is not None:
        print(f"INVOICE: Due={i_row['due_date']} (Issue={i_row['issue_date']}) | Amt={i_row['amount']} | Vendor='{i_row['vendor']}' | Desc='{i_row.get('description', '')}'")

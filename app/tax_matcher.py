import pandas as pd
import numpy as np

TAX_RULES = {
    "Revenue - Services": [
        "consulting revenue", "service fee", "client payment", "retainer", 
        "invoiced service", "platform revenue", "sales", "customer payment", "services"
    ],
    "Revenue - Interest": [
        "interest income", "yield", "dividend", "interest deposit", "interest earned"
    ],
    "COGS - Materials": [
        "packaging", "industrial materials", "raw materials", "globex", "acme industrial",
        "supplies for production", "packaging supplies", "materials"
    ],
    "COGS - Freight": [
        "freight", "shipping", "fedex", "ups", "logistics", "cargo", "carrier"
    ],
    "Marketing & Advertising": [
        "hooli marketing", "marketing", "advertising", "meta", "google ads", 
        "linkedin ads", "billboard", "pr agency", "promotions", "ad spend"
    ],
    "Bank Fees": [
        "first national bank", "wire fee", "bank charge", "service charge", 
        "monthly fee", "overdraft", "banking fee", "processing fee"
    ],
    "Utilities": [
        "verizon", "at&t", "comcast", "coned", "electric", "internet", 
        "utility", "water", "telecom", "broadband", "power"
    ],
    "Rent - Office": [
        "wework", "realty", "properties", "rent", "lease", "storage", 
        "facilities", "office space", "workspace"
    ],
    "Travel & Meals": [
        "uber", "lyft", "airline", "delta", "united", "hotel", "marriott", 
        "restaurant", "cafe", "airfare", "travel", "meals", "offsite hotel"
    ],
    "Software & Subscriptions": [
        "aws", "github", "slack", "google cloud", "openai", "atlassian", 
        "zoom", "notion", "adobe", "microsoft", "software", "saas", "subscription"
    ],
    "Insurance": [
        "hiscox", "travelers", "chubb", "geico", "insurance", "policy", "premium", "coverage"
    ],
    "Payroll - Salaries": [
        "salary", "salaries", "biweekly payroll", "wages", "payroll services inc", "direct deposit"
    ],
    "Payroll - Benefits": [
        "health", "benefits", "rippling benefits", "gusto benefits", "dental", "vision", "401k"
    ],
    "Professional Services": [
        "legal", "deloitte", "pwc", "consulting", "attorney", "cpa", "advisory", 
        "audit", "accounting firm", "law"
    ],
    "Office Supplies": [
        "office depot", "staples", "desk", "printer consumables", "consumables", 
        "printer", "toner", "paper"
    ],
    "Equipment & Depreciation": [
        "depreciation", "equipment", "macbook", "laptop", "server hardware", "deprec"
    ]
}

def classify_tax_line(description: str, vendor: str = "", amount: float = 0.0) -> tuple:
    text = f"{str(description)} {str(vendor)}".lower()
    amt = float(amount)

    # Inflows
    if amt > 0 and ("interest" in text or "yield" in text):
        return "Revenue - Interest", 0.95, "Interest keyword + positive flow"
    if amt > 0 and any(k in text for k in ["revenue", "client", "customer", "invoice paid", "service"]):
        return "Revenue - Services", 0.90, "Revenue pattern + positive flow"

    # Specific precedence ordering (e.g. COGS Materials before general Office Supplies)
    for category in [
        "COGS - Materials", "COGS - Freight", "Marketing & Advertising", 
        "Bank Fees", "Software & Subscriptions", "Rent - Office", 
        "Utilities", "Payroll - Salaries", "Payroll - Benefits", 
        "Travel & Meals", "Insurance", "Professional Services", 
        "Office Supplies", "Equipment & Depreciation"
    ]:
        keywords = TAX_RULES[category]
        if any(kw in text for kw in keywords):
            return category, 0.90, f"Matched rule: {category}"

    return "Unclassified Expense", 0.30, "No keyword pattern matched"

def build_unified_ledger(bank_df, ledger_df, invoice_df, bl_res, bi_res):
    unified_records = []
    
    processed_bank = set()
    processed_ledger = set()
    processed_invoices = set()

    # 1. Process Bank transactions with their matches
    for _, b_row in bank_df.iterrows():
        b_ref = b_row['bank_ref']
        processed_bank.add(b_ref)

        l_match = bl_res[(bl_res['bank_ref'] == b_ref) & (bl_res['status'] == 'MATCHED')]
        matched_journal_id = l_match['journal_id'].iloc[0] if not l_match.empty else None
        if matched_journal_id:
            processed_ledger.add(matched_journal_id)

        i_match = bi_res[(bi_res['bank_ref'] == b_ref) & (bi_res['status'] == 'MATCHED')]
        matched_inv_num = i_match['invoice_number'].iloc[0] if not i_match.empty else None
        if matched_inv_num:
            processed_invoices.add(matched_inv_num)

        l_row = ledger_df[ledger_df['journal_id'] == matched_journal_id].iloc[0] if matched_journal_id else None
        i_row = invoice_df[invoice_df['invoice_number'] == matched_inv_num].iloc[0] if matched_inv_num else None

        desc = b_row.get('description', '')
        vendor = ""
        amount = b_row.get('amount')
        date = b_row.get('date')

        if i_row is not None:
            vendor = i_row.get('vendor', '')
            desc = f"{desc} {i_row.get('description', '')}"
        elif l_row is not None:
            vendor = l_row.get('vendor', '')
            desc = f"{desc} {l_row.get('description', '')}"

        tax_line, conf, reason = classify_tax_line(desc, vendor, amount)

        unified_records.append({
            'bank_ref': b_ref,
            'journal_id': matched_journal_id,
            'invoice_number': matched_inv_num,
            'date': date,
            'amount': amount,
            'vendor': vendor,
            'description': desc.strip(),
            'tax_line': tax_line,
            'tax_confidence': conf,
            'tax_reason': reason,
            'match_source_count': 1 + (1 if matched_journal_id else 0) + (1 if matched_inv_num else 0)
        })

    # 2. Add orphan Ledger records
    for _, l_row in ledger_df.iterrows():
        j_id = l_row['journal_id']
        if j_id not in processed_ledger:
            processed_ledger.add(j_id)
            desc = l_row.get('description', '')
            vendor = l_row.get('vendor', '')
            amt = l_row.get('amount', 0.0)
            tax_line, conf, reason = classify_tax_line(desc, vendor, amt)
            unified_records.append({
                'bank_ref': None,
                'journal_id': j_id,
                'invoice_number': None,
                'date': l_row.get('date'),
                'amount': amt,
                'vendor': vendor,
                'description': desc,
                'tax_line': tax_line,
                'tax_confidence': conf,
                'tax_reason': reason,
                'match_source_count': 1
            })

    # 3. Add orphan Invoice records
    for _, i_row in invoice_df.iterrows():
        inv_num = i_row['invoice_number']
        if inv_num not in processed_invoices:
            processed_invoices.add(inv_num)
            desc = i_row.get('description', '')
            vendor = i_row.get('vendor', '')
            amt = i_row.get('amount', 0.0)
            tax_line, conf, reason = classify_tax_line(desc, vendor, amt)
            unified_records.append({
                'bank_ref': None,
                'journal_id': None,
                'invoice_number': inv_num,
                'date': i_row.get('issue_date', i_row.get('due_date')),
                'amount': amt,
                'vendor': vendor,
                'description': desc,
                'tax_line': tax_line,
                'tax_confidence': conf,
                'tax_reason': reason,
                'match_source_count': 1
            })

    return pd.DataFrame(unified_records)
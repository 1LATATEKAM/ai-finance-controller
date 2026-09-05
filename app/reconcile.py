import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from datetime import datetime

def text_similarity(a: str, b: str) -> float:
    if not a or not b or pd.isna(a) or pd.isna(b):
        return 0.0
    return SequenceMatcher(None, str(a).lower().strip(), str(b).lower().strip()).ratio()

def parse_date(d_val):
    if pd.isna(d_val):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(d_val).strip(), fmt)
        except ValueError:
            pass
    return None

def score_date(d1, d2, max_days=7) -> float:
    dt1, dt2 = parse_date(d1), parse_date(d2)
    if not dt1 or not dt2:
        return 0.0
    diff = abs((dt1 - dt2).days)
    if diff == 0:
        return 1.0
    elif diff <= max_days:
        return max(0.0, 1.0 - (diff / (max_days + 1)))
    return 0.0

def score_amount(a1, a2) -> float:
    try:
        val1, val2 = abs(float(a1)), abs(float(a2))
    except (ValueError, TypeError):
        return 0.0
    
    if val1 == 0 and val2 == 0:
        return 1.0
    diff = abs(val1 - val2)
    if diff == 0:
        return 1.0
    # Allow fee/rounding tolerances (up to $25 or 1%)
    if diff <= 25.0 or (diff / max(val1, val2) <= 0.015):
        return 0.85
    return 0.0

def reconcile_bank_to_ledger(bank_df: pd.DataFrame, ledger_df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for _, b_row in bank_df.iterrows():
        b_ref = b_row['bank_ref']
        b_amt = b_row['amount']
        b_desc = b_row['description']
        b_date = b_row['date']

        candidates = []
        for _, l_row in ledger_df.iterrows():
            amt_s = score_amount(b_amt, l_row['amount'])
            if amt_s == 0.0:
                continue

            date_s = score_date(b_date, l_row['date'], max_days=5)
            # Combine account code, description, and vendor if present
            l_desc = f"{l_row.get('description', '')} {l_row.get('vendor', '')}"
            txt_s = text_similarity(b_desc, l_desc)
            
            # Boost score if vendor text is a subset
            if str(b_desc).lower() in l_desc.lower() or l_desc.lower() in str(b_desc).lower():
                txt_s = max(txt_s, 0.8)

            total_score = (amt_s * 0.50) + (date_s * 0.25) + (txt_s * 0.25)
            candidates.append({
                'journal_id': l_row['journal_id'],
                'score': total_score,
                'amt_s': amt_s,
                'date_s': date_s,
                'txt_s': txt_s
            })

        if not candidates:
            results.append({'bank_ref': b_ref, 'journal_id': None, 'status': 'UNMATCHED', 'confidence': 0.0})
            continue

        candidates.sort(key=lambda x: x['score'], reverse=True)
        top = candidates[0]
        runner_up = candidates[1] if len(candidates) > 1 else None

        # Disambiguation check
        if runner_up and abs(top['score'] - runner_up['score']) < 0.05 and top['score'] >= 0.70:
            results.append({'bank_ref': b_ref, 'journal_id': top['journal_id'], 'status': 'AMBIGUOUS', 'confidence': round(top['score'], 3)})
        elif top['score'] >= 0.75:
            results.append({'bank_ref': b_ref, 'journal_id': top['journal_id'], 'status': 'MATCHED', 'confidence': round(top['score'], 3)})
        elif top['score'] >= 0.50:
            results.append({'bank_ref': b_ref, 'journal_id': top['journal_id'], 'status': 'REVIEW', 'confidence': round(top['score'], 3)})
        else:
            results.append({'bank_ref': b_ref, 'journal_id': None, 'status': 'UNMATCHED', 'confidence': round(top['score'], 3)})

    return pd.DataFrame(results)

def reconcile_bank_to_invoices(bank_df: pd.DataFrame, inv_df: pd.DataFrame, ledger_res_df: pd.DataFrame = None, ledger_df: pd.DataFrame = None) -> pd.DataFrame:
    results = []
    for _, b_row in bank_df.iterrows():
        b_ref = b_row['bank_ref']
        b_amt = b_row['amount']
        b_desc = b_row['description']
        b_date = b_row['date']

        candidates = []
        for _, i_row in inv_df.iterrows():
            amt_s = score_amount(b_amt, i_row['amount'])
            if amt_s == 0.0:
                continue

            # Invoices have both issue_date and due_date
            date_s_issue = score_date(b_date, i_row.get('issue_date'), max_days=5)
            date_s_due = score_date(b_date, i_row.get('due_date'), max_days=5)
            date_s = max(date_s_issue, date_s_due)

            inv_text = f"{i_row.get('vendor', '')} {i_row.get('description', '')}"
            txt_s = text_similarity(b_desc, inv_text)
            if str(b_desc).lower() in inv_text.lower() or str(i_row.get('vendor', '')).lower() in str(b_desc).lower():
                txt_s = max(txt_s, 0.85)

            # Heuristic: exact amount + exact issue_date (e.g. POS purchase / clean)
            if amt_s == 1.0 and date_s_issue == 1.0:
                score = 0.85 + (txt_s * 0.15)
            else:
                score = (amt_s * 0.50) + (date_s * 0.25) + (txt_s * 0.25)

            candidates.append({
                'invoice_number': i_row['invoice_number'],
                'score': score,
                'amt_s': amt_s,
                'date_s': date_s,
                'txt_s': txt_s
            })

        if not candidates:
            results.append({'bank_ref': b_ref, 'invoice_number': None, 'status': 'UNMATCHED', 'confidence': 0.0})
            continue

        candidates.sort(key=lambda x: x['score'], reverse=True)
        top = candidates[0]
        runner_up = candidates[1] if len(candidates) > 1 else None

        if runner_up and abs(top['score'] - runner_up['score']) < 0.04 and top['score'] >= 0.70:
            results.append({'bank_ref': b_ref, 'invoice_number': top['invoice_number'], 'status': 'AMBIGUOUS', 'confidence': round(top['score'], 3)})
        elif top['score'] >= 0.75:
            results.append({'bank_ref': b_ref, 'invoice_number': top['invoice_number'], 'status': 'MATCHED', 'confidence': round(top['score'], 3)})
        elif top['score'] >= 0.50:
            results.append({'bank_ref': b_ref, 'invoice_number': top['invoice_number'], 'status': 'REVIEW', 'confidence': round(top['score'], 3)})
        else:
            results.append({'bank_ref': b_ref, 'invoice_number': None, 'status': 'UNMATCHED', 'confidence': round(top['score'], 3)})

    return pd.DataFrame(results)
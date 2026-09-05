import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
import numpy as np

def evaluate_reconciliation(
    preds_path: str,
    gt_path: str = "data/ground_truth.csv",
    source_gt_col: str = "bank_ref",
    target_gt_col: str = "journal_id",
    source_pred_col: str = "bank_ref",
    target_pred_col: str = None
):
    gt = pd.read_csv(gt_path)
    preds = pd.read_csv(preds_path)

    if target_pred_col is None:
        target_pred_col = target_gt_col

    print(f"\n=======================================================")
    print(f" EVALUATING: {preds_path}")
    print(f" Source: '{source_pred_col}' -> Target: '{target_pred_col}'")
    print(f"=======================================================")

    valid_gt = gt.dropna(subset=[source_gt_col, target_gt_col]).copy()
    valid_gt[source_gt_col] = valid_gt[source_gt_col].astype(str).str.strip()
    valid_gt[target_gt_col] = valid_gt[target_gt_col].astype(str).str.strip()

    true_pairs = dict(zip(valid_gt[source_gt_col], valid_gt[target_gt_col]))
    total_true_matches = len(true_pairs)

    preds[source_pred_col] = preds[source_pred_col].astype(str).str.strip()
    preds[target_pred_col] = preds[target_pred_col].astype(str).str.strip()

    status_col = [c for c in preds.columns if 'status' in c.lower()][0]

    matched = preds[preds[status_col].str.upper() == 'MATCHED']
    unmatched = preds[preds[status_col].str.upper() == 'UNMATCHED']
    reviews = preds[preds[status_col].str.upper() == 'REVIEW'] if 'REVIEW' in preds[status_col].values else pd.DataFrame()
    ambiguous = preds[preds[status_col].str.upper() == 'AMBIGUOUS'] if 'AMBIGUOUS' in preds[status_col].values else pd.DataFrame()

    true_positives = 0
    false_positives = 0

    for _, row in matched.iterrows():
        s_val = row[source_pred_col]
        t_val = row[target_pred_col]

        if s_val in true_pairs and true_pairs[s_val] == t_val:
            true_positives += 1
        else:
            false_positives += 1

    precision = (true_positives / len(matched)) if len(matched) > 0 else 0.0
    recall = (true_positives / total_true_matches) if total_true_matches > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    print(f"Total Records Tested      : {len(preds)}")
    print(f"Expected True Pairs       : {total_true_matches}")
    print(f"-------------------------------------------------------")
    print(f"Matches Declared (Engine) : {len(matched)}")
    print(f"  └─ True Positives (TP)  : {true_positives}")
    print(f"  └─ False Positives (FP) : {false_positives}")
    print(f"-------------------------------------------------------")
    print(f"Precision                 : {precision:.2%}")
    print(f"Recall (Coverage)         : {recall:.2%}")
    print(f"F1 Score                  : {f1:.2%}")
    print(f"-------------------------------------------------------")
    print(f"Exception Breakdown:")
    print(f"  ├─ Review Queue         : {len(reviews)}")
    print(f"  ├─ Ambiguous Queue      : {len(ambiguous)}")
    print(f"  └─ Unmatched Queue      : {len(unmatched)}")
    print(f"=======================================================\n")

def evaluate_tax_and_closure(canonical_path="data/canonical_ledger.csv", gt_path="data/ground_truth.csv"):
    gt = pd.read_csv(gt_path)
    pred = pd.read_csv(canonical_path)

    print("\n=======================================================")
    print(" TAX-LINE CLASSIFICATION & LOOP CLOSURE EVALUATION")
    print("=======================================================")

    correct_tax = 0
    total_evaluable = 0
    exceptions = []

    for _, row in pred.iterrows():
        b_ref = row.get('bank_ref')
        j_id = row.get('journal_id')
        inv_num = row.get('invoice_number')

        gt_match = pd.DataFrame()
        if pd.notna(b_ref) and 'bank_ref' in gt.columns:
            gt_match = gt[gt['bank_ref'] == b_ref]
        elif pd.notna(j_id) and 'journal_id' in gt.columns:
            gt_match = gt[gt['journal_id'] == j_id]
        elif pd.notna(inv_num) and 'invoice_number' in gt.columns:
            gt_match = gt[gt['invoice_number'] == inv_num]

        if not gt_match.empty:
            total_evaluable += 1
            true_tax = str(gt_match.iloc[0].get('tax_line', '')).strip().lower()
            pred_tax = str(row.get('tax_line', '')).strip().lower()

            if true_tax == pred_tax:
                correct_tax += 1
            else:
                exceptions.append({
                    'ref': b_ref or j_id or inv_num,
                    'pred': row.get('tax_line'),
                    'true': gt_match.iloc[0].get('tax_line'),
                    'desc': row.get('description')[:40] if row.get('description') else ''
                })

    tax_acc = (correct_tax / total_evaluable) if total_evaluable > 0 else 0.0

    print(f"Total Canonical Records Checked : {total_evaluable}")
    print(f"Correct Tax Line Assignments    : {correct_tax}")
    print(f"Tax-Line Accuracy Rate          : {tax_acc:.2%}")
    print(f"Total Exceptions / Discrepancies: {len(exceptions)}")
    print("-------------------------------------------------------")
    if exceptions:
        print("Sample Exceptions (first 5):")
        for ex in exceptions[:5]:
            print(f"  [{ex['ref']}] Pred: '{ex['pred']}' | True: '{ex['true']}' | Desc: '{ex['desc']}'")
    print("=======================================================\n")

if __name__ == "__main__":
    evaluate_reconciliation("data/bank_ledger_results.csv", "data/ground_truth.csv", "bank_ref", "journal_id")
    evaluate_reconciliation("data/bank_invoice_results.csv", "data/ground_truth.csv", "bank_ref", "invoice_number")
    evaluate_tax_and_closure()
import pandas as pd
import numpy as np

def evaluate_reconciliation(
    preds_path: str,
    gt_path: str = "data/ground_truth.csv",
    source_gt_col: str = "bank_ref",
    target_gt_col: str = "journal_id",
    source_pred_col: str = None,
    target_pred_col: str = None
):
    gt = pd.read_csv(gt_path)
    preds = pd.read_csv(preds_path)

    # Auto-detect prediction columns if not explicitly provided
    if source_pred_col is None:
        possible_src = [c for c in preds.columns if 'bank' in c.lower() or 'ref' in c.lower() or 'src' in c.lower()]
        source_pred_col = possible_src[0] if possible_src else preds.columns[0]

    if target_pred_col is None:
        possible_tgt = [c for c in preds.columns if any(k in c.lower() for k in ['journal', 'ledger', 'invoice', 'matched', 'target'])]
        target_pred_col = possible_tgt[0] if possible_tgt else preds.columns[1]

    print(f"\n=======================================================")
    print(f" EVALUATING: {preds_path}")
    print(f" Matching '{source_pred_col}' -> '{target_pred_col}'")
    print(f" Ground Truth: '{source_gt_col}' -> '{target_gt_col}'")
    print(f"=======================================================")

    # Filter GT to rows that actually have both items present
    valid_gt = gt.dropna(subset=[source_gt_col, target_gt_col]).copy()
    valid_gt[source_gt_col] = valid_gt[source_gt_col].astype(str).str.strip()
    valid_gt[target_gt_col] = valid_gt[target_gt_col].astype(str).str.strip()

    # Ground truth mapping: source -> target
    true_pairs = dict(zip(valid_gt[source_gt_col], valid_gt[target_gt_col]))
    total_true_matches = len(true_pairs)

    # Normalize prediction columns
    preds[source_pred_col] = preds[source_pred_col].astype(str).str.strip()
    preds[target_pred_col] = preds[target_pred_col].astype(str).str.strip()

    # Standardize status column lookup
    status_col = [c for c in preds.columns if 'status' in c.lower()][0]

    matched = preds[preds[status_col].str.upper() == 'MATCHED']
    reviews = preds[preds[status_col].str.upper() == 'REVIEW']
    ambiguous = preds[preds[status_col].str.upper() == 'AMBIGUOUS']
    unmatched = preds[preds[status_col].str.upper() == 'UNMATCHED']

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

    print(f"Total Source Rows Checked : {len(preds)}")
    print(f"Expected True Pairs in GT : {total_true_matches}")
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

if __name__ == "__main__":
    # 1. Bank -> Ledger Evaluation
    evaluate_reconciliation(
        preds_path="data/bank_ledger_results.csv",
        source_gt_col="bank_ref",
        target_gt_col="journal_id"
    )

    # 2. Bank -> Invoice Evaluation
    evaluate_reconciliation(
        preds_path="data/bank_invoice_results.csv",
        source_gt_col="bank_ref",
        target_gt_col="invoice_number"
    )
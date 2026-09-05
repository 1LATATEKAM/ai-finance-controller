import pandas as pd
from rapidfuzz.fuzz import ratio


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------

def normalize_text(text):
    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Remove common punctuation
    for char in [",", ".", "-", "_", "/", "(", ")", ":"]:
        text = text.replace(char, " ")

    # Remove extra spaces
    return " ".join(text.split())


# ---------------------------------------------------------
# TEXT SIMILARITY
# ---------------------------------------------------------

def text_similarity(text1, text2):
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0

    return ratio(text1, text2) / 100


# ---------------------------------------------------------
# AMOUNT SIMILARITY
# ---------------------------------------------------------

def amount_similarity(amount1, amount2, tolerance=0.05):
    """
    Bank transactions may have negative values while
    ledger/invoice amounts are positive.

    Therefore we compare absolute values.
    """

    try:
        amount1 = abs(float(amount1))
        amount2 = abs(float(amount2))
    except:
        return 0

    difference = abs(amount1 - amount2)

    # Exact / almost exact
    if difference <= tolerance:
        return 1.0

    # Gradually decrease similarity
    maximum = max(amount1, amount2)

    if maximum == 0:
        return 1.0

    similarity = 1 - (difference / maximum)

    return max(0, similarity)


# ---------------------------------------------------------
# DATE SIMILARITY
# ---------------------------------------------------------

def date_similarity(date1, date2):
    try:
        date1 = pd.to_datetime(date1)
        date2 = pd.to_datetime(date2)

        difference = abs((date1 - date2).days)

        if difference == 0:
            return 1.0

        elif difference == 1:
            return 0.9

        elif difference == 2:
            return 0.75

        elif difference <= 5:
            return 0.5

        else:
            return 0.0

    except:
        return 0


# ---------------------------------------------------------
# CALCULATE MATCH SCORE
# ---------------------------------------------------------

def calculate_score(bank_row, other_row, description_column,
                    amount_column, date_column):

    text_score = text_similarity(
        bank_row["description"],
        other_row[description_column]
    )

    amount_score = amount_similarity(
        bank_row["amount"],
        other_row[amount_column]
    )

    date_score = date_similarity(
        bank_row["date"],
        other_row[date_column]
    )

    # Weighted score
    final_score = (
        text_score * 0.40 +
        amount_score * 0.40 +
        date_score * 0.20
    )

    return {
        "text_score": round(text_score, 3),
        "amount_score": round(amount_score, 3),
        "date_score": round(date_score, 3),
        "confidence": round(final_score, 3)
    }


# ---------------------------------------------------------
# MATCH BANK → LEDGER
# ---------------------------------------------------------

def match_bank_to_ledger(bank_df, ledger_df):

    results = []

    for _, bank_row in bank_df.iterrows():

        candidates = []

        for _, ledger_row in ledger_df.iterrows():

            scores = calculate_score(
                bank_row,
                ledger_row,
                "description",
                "amount",
                "date"
            )

            candidates.append({
                "bank_ref": bank_row["bank_ref"],
                "journal_id": ledger_row["journal_id"],
                **scores
            })

        # Sort candidates by confidence
        candidates.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )

        best = candidates[0]

        # Check second-best candidate
        second_best = (
            candidates[1]["confidence"]
            if len(candidates) > 1
            else 0
        )

        confidence = best["confidence"]

        # ---------------------------------------------
        # DECISION LOGIC
        # ---------------------------------------------

        if confidence >= 0.80:

            # Strong match
            status = "MATCHED"
            reason = "High confidence match"

        elif confidence >= 0.60:

            # Could be correct but needs review
            if confidence - second_best < 0.05:
                status = "AMBIGUOUS"
                reason = "Multiple candidates have similar scores"
            else:
                status = "REVIEW"
                reason = "Moderate confidence match"

        else:

            status = "UNMATCHED"
            reason = "No sufficiently strong candidate"

        results.append({
            "bank_ref": best["bank_ref"],
            "journal_id": best["journal_id"],
            "text_score": best["text_score"],
            "amount_score": best["amount_score"],
            "date_score": best["date_score"],
            "confidence": confidence,
            "status": status,
            "reason": reason
        })

    return pd.DataFrame(results)


# ---------------------------------------------------------
# MATCH BANK → INVOICE
# ---------------------------------------------------------

def match_bank_to_invoice(bank_df, invoice_df):

    results = []

    for _, bank_row in bank_df.iterrows():

        candidates = []

        for _, invoice_row in invoice_df.iterrows():

            scores = calculate_score(
                bank_row,
                invoice_row,
                "description",
                "amount",
                "issue_date"
            )

            candidates.append({
                "bank_ref": bank_row["bank_ref"],
                "invoice_number": invoice_row["invoice_number"],
                **scores
            })

        candidates.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )

        best = candidates[0]

        second_best = (
            candidates[1]["confidence"]
            if len(candidates) > 1
            else 0
        )

        confidence = best["confidence"]

        if confidence >= 0.80:
            status = "MATCHED"
            reason = "High confidence match"

        elif confidence >= 0.60:

            if confidence - second_best < 0.05:
                status = "AMBIGUOUS"
                reason = "Multiple candidates have similar scores"
            else:
                status = "REVIEW"
                reason = "Moderate confidence match"

        else:
            status = "UNMATCHED"
            reason = "No sufficiently strong candidate"

        results.append({
            "bank_ref": best["bank_ref"],
            "invoice_number": best["invoice_number"],
            "text_score": best["text_score"],
            "amount_score": best["amount_score"],
            "date_score": best["date_score"],
            "confidence": confidence,
            "status": status,
            "reason": reason
        })

    return pd.DataFrame(results)
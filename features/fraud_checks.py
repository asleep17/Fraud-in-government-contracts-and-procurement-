from typing import List

import pandas as pd


# New fraud checks for mock schema
def flag_low_bidder_count(df: pd.DataFrame, min_bidders: int = 2) -> pd.DataFrame:
    """Flag contracts with suspiciously low bidder count."""
    if "bidder_count" not in df.columns:
        return df.iloc[0:0]
    return df[df["bidder_count"] <= min_bidders].copy()

def flag_high_cost_variance(df: pd.DataFrame, threshold: float = 20.0) -> pd.DataFrame:
    """Flag contracts with high cost variance percentage."""
    if "cost_variance_pct" not in df.columns:
        return df.iloc[0:0]
    return df[df["cost_variance_pct"] >= threshold].copy()

def flag_payment_discrepancy(df: pd.DataFrame, threshold: float = 100000.0) -> pd.DataFrame:
    """Flag contracts with large payment discrepancy."""
    if "payment_discrepancy" not in df.columns:
        return df.iloc[0:0]
    return df[df["payment_discrepancy"] >= threshold].copy()

def flag_red_flag_entity(df: pd.DataFrame) -> pd.DataFrame:
    if "is_red_flag_entity" not in df.columns:
        return df.iloc[0:0]
    return df[df["is_red_flag_entity"] == True].copy()

def flag_blacklisted_contractor(df: pd.DataFrame) -> pd.DataFrame:
    if "is_blacklisted_contractor" not in df.columns:
        return df.iloc[0:0]
    return df[df["is_blacklisted_contractor"] == True].copy()

# Keep legacy checks for compatibility
def flag_high_value(df: pd.DataFrame, amount_col: str = "contract_amount", quantile: float = 0.99) -> pd.DataFrame:
    if amount_col not in df.columns:
        return df.iloc[0:0]
    thresh = df[amount_col].dropna().quantile(quantile)
    return df[df[amount_col] >= thresh].copy()

def flag_repeated_vendors(df: pd.DataFrame, vendor_col: str = "vendor", min_count: int = 5) -> pd.DataFrame:
    if vendor_col not in df.columns:
        return df.iloc[0:0]
    counts = df[vendor_col].value_counts()
    repeated = counts[counts >= min_count].index.tolist()
    return df[df[vendor_col].isin(repeated)].copy()

def flag_missing_ids(df: pd.DataFrame, id_cols=None) -> pd.DataFrame:
    if id_cols is None:
        id_cols = ["contract_code", "vat_no1"]
    missing_any = df[id_cols].isna().any(axis=1) if set(id_cols).issubset(df.columns) else pd.Series([False]*len(df))
    return df[missing_any].copy()

def combined_suspicion(df: pd.DataFrame) -> pd.DataFrame:
    flags = pd.DataFrame(index=df.index)
    flags["high_value"] = False
    flags["repeated_vendor"] = False
    flags["missing_id"] = False
    flags["low_bidder_count"] = False
    flags["high_cost_variance"] = False
    flags["payment_discrepancy"] = False
    flags["red_flag_entity"] = False
    flags["blacklisted_contractor"] = False

    if "contract_amount" in df.columns:
        thresh = df["contract_amount"].dropna().quantile(0.99)
        flags.loc[df["contract_amount"] >= thresh, "high_value"] = True

    if "vendor" in df.columns:
        vc = df["vendor"].value_counts()
        repeated = vc[vc >= 5].index
        flags.loc[df["vendor"].isin(repeated), "repeated_vendor"] = True

    id_cols = [c for c in ["contract_code", "vat_no1"] if c in df.columns]
    if id_cols:
        flags.loc[df[id_cols].isna().any(axis=1), "missing_id"] = True

    if "bidder_count" in df.columns:
        flags.loc[df["bidder_count"] <= 2, "low_bidder_count"] = True

    if "cost_variance_pct" in df.columns:
        flags.loc[df["cost_variance_pct"] >= 20.0, "high_cost_variance"] = True

    if "payment_discrepancy" in df.columns:
        flags.loc[df["payment_discrepancy"] >= 100000.0, "payment_discrepancy"] = True

    if "is_red_flag_entity" in df.columns:
        flags.loc[df["is_red_flag_entity"] == True, "red_flag_entity"] = True

    if "is_blacklisted_contractor" in df.columns:
        flags.loc[df["is_blacklisted_contractor"] == True, "blacklisted_contractor"] = True

    flags["suspicious"] = flags.any(axis=1)
    out = df.copy()
    out = out.assign(**flags)
    return out[out["suspicious"]]


RISK_LEVEL_THRESHOLDS = [
    (70, "Critical"),
    (45, "High"),
    (25, "Medium"),
    (0, "Low"),
]


def _risk_level(score: float) -> str:
    for threshold, label in RISK_LEVEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "Low"


def _get_numeric(row: pd.Series, column: str):
    value = row.get(column)
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_bool(row: pd.Series, column: str) -> bool:
    value = row.get(column)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def score_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Apply a rule-based fraud risk scoring model built for the mock dataset."""
    if df.empty:
        empty_scores = pd.DataFrame(
            {
                "risk_score": pd.Series(dtype=float),
                "risk_level": pd.Series(dtype=str),
                "risk_reasons": pd.Series(dtype=str),
                "risk_triggers": pd.Series(dtype=int),
            }
        )
        return pd.concat([df, empty_scores], axis=1)

    def _score_row(row: pd.Series) -> pd.Series:
        score = 0
        reasons: List[str] = []

        def add(points: int, reason: str):
            nonlocal score
            score += points
            reasons.append(reason)

        bidder_count = _get_numeric(row, "bidder_count")
        if bidder_count is not None:
            if bidder_count <= 2:
                add(20, "Low bidder count (≤2)")
            elif bidder_count <= 4:
                add(10, "Limited bidder competition (≤4)")

        cost_variance = _get_numeric(row, "cost_variance_pct")
        if cost_variance is not None:
            if cost_variance >= 15:
                add(15, "Cost variance ≥15% over estimate")
            if cost_variance <= -15:
                add(10, "Cost variance ≤-15% (aggressive underbid)")

        payment_gap = _get_numeric(row, "payment_discrepancy")
        if payment_gap is not None:
            abs_gap = abs(payment_gap)
            if abs_gap >= 1_000_000:
                add(20, "Payment discrepancy ≥ NPR 1M")
            elif abs_gap >= 500_000:
                add(12, "Payment discrepancy ≥ NPR 500k")

        contract_amount = _get_numeric(row, "contract_amount")
        estimate = _get_numeric(row, "estimatedCost")
        if contract_amount and estimate:
            diff_pct = ((contract_amount - estimate) / estimate) * 100
            if diff_pct >= 25:
                add(10, "Contract value ≥25% above estimate")
            elif diff_pct <= -20:
                add(8, "Contract awarded ≥20% below estimate")

        actual_payment = _get_numeric(row, "actual_payment_made")
        if actual_payment is not None and contract_amount:
            overpay_pct = ((actual_payment - contract_amount) / contract_amount) * 100
            if overpay_pct >= 10:
                add(15, "Payments exceed contract amount by ≥10%")
            elif overpay_pct <= -20:
                add(8, "Payments lag contract amount by ≥20%")

        completion_pct = _get_numeric(row, "percentageOfCompletion")
        status = str(row.get("status", "")).strip().lower()
        if completion_pct is not None:
            if status == "completed" and completion_pct < 80:
                add(15, "Marked completed with <80% progress")
            if status in {"in-progress", "delayed"} and completion_pct >= 95:
                add(8, "Near completion but not closed")
            if status == "delayed" and completion_pct < 50:
                add(10, "Delayed with <50% progress")

        if _get_bool(row, "is_red_flag_entity"):
            add(12, "Awarded to a red-flagged entity")
        if _get_bool(row, "is_blacklisted_contractor"):
            add(30, "Blacklisted contractor involved")

        method = str(row.get("procurement_method", "")).strip().lower()
        if (
            method in {"direct", "shopping", "rfq"}
            and contract_amount is not None
            and contract_amount >= 10_000_000
        ):
            add(12, "High-value contract via limited competition method")

        duration_days = _get_numeric(row, "contract_duration_days")
        if duration_days is not None and method in {"shopping", "rfq"} and duration_days >= 180:
            add(6, "Short-form method used for long-duration contract")

        trigger_count = len(reasons)
        return pd.Series(
            {
                "risk_score": float(score),
                "risk_level": _risk_level(score),
                "risk_reasons": "; ".join(reasons) if reasons else "No apparent red flags",
                "risk_triggers": trigger_count,
            }
        )

    scores = df.apply(_score_row, axis=1)
    return pd.concat([df.reset_index(drop=True), scores.reset_index(drop=True)], axis=1)

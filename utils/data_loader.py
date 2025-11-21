import pandas as pd
from typing import Optional



def load_data(path: str = "combined_contract_data.csv") -> pd.DataFrame:
    """Load contract CSV and do basic cleaning for both real and mock schemas."""
    df = pd.read_csv(path, dtype=str, na_values=["", "--Select source of Fund --", "--Select Country--", "--Select Bidding Process --"]) 

    # Numeric conversions (support both schemas)
    numeric_cols = [
        "contract_amount",
        "totalPayment",
        "estimatedCost",
        "outstandingValue",
        "cost_variance_pct",
        "bidder_count",
        "contract_duration_days",
        "payment_discrepancy",
        "actual_payment_made",
        "percentageOfCompletion",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse key dates
    for date_col in ["contractDate", "startDate", "deliveryDate", "postValidationDate", "endOrCompleteDate"]:
        if date_col in df.columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
            except Exception:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Standard vendor column choices
    if "contractorName1" in df.columns:
        df["vendor"] = df["contractorName1"].fillna(df.get("contractorName2", "")).fillna(df.get("contractorName3", ""))
    elif "contractorName" in df.columns:
        df["vendor"] = df["contractorName"]
    else:
        df["vendor"] = ""

    # Boolean flags
    for col in ["is_red_flag_entity", "is_blacklisted_contractor"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().map({"true": True, "1": True, "yes": True, "y": True, "false": False, "0": False, "no": False, "n": False}).fillna(False)

    return df


def sample_data(path: str = "combined_contract_data.csv", n: int = 5) -> pd.DataFrame:
    df = load_data(path)
    return df.head(n)

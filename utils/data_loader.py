import pandas as pd
from typing import Optional


def load_data(path: str = "combined_contract_data.csv") -> pd.DataFrame:
    """Load the combined contract CSV and do basic cleaning.

    - Coerce numeric fields
    - Parse dates (trying day-first format)
    - Fill simple missing values
    """
    df = pd.read_csv(path, dtype=str, na_values=["", "--Select source of Fund --", "--Select Country--", "--Select Bidding Process --"]) 

    # Numeric conversions
    for col in ["contract_amount", "totalPayment", "estimatedCost", "outstandingValue"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse key dates if present
    for date_col in ["contractDate", "startDate", "deliveryDate", "postValidationDate"]:
        if date_col in df.columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
            except Exception:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Standard vendor column choices
    if "contractorName1" in df.columns:
        df["vendor"] = df["contractorName1"].fillna(df.get("contractorName2", "")).fillna(df.get("contractorName3", ""))
    else:
        df["vendor"] = df.get("contractorName", "")

    return df


def sample_data(path: str = "combined_contract_data.csv", n: int = 5) -> pd.DataFrame:
    df = load_data(path)
    return df.head(n)

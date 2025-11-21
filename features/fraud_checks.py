import pandas as pd


def flag_high_value(df: pd.DataFrame, amount_col: str = "contract_amount", quantile: float = 0.99) -> pd.DataFrame:
    """Flag contracts whose amount is in the top `quantile`.

    Returns a dataframe of suspicious high-value contracts.
    """
    if amount_col not in df.columns:
        return df.iloc[0:0]
    thresh = df[amount_col].dropna().quantile(quantile)
    return df[df[amount_col] >= thresh].copy()


def flag_repeated_vendors(df: pd.DataFrame, vendor_col: str = "vendor", min_count: int = 5) -> pd.DataFrame:
    """Find vendors with many contracts (could indicate channeling)"""
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
    """Create a combined 'suspicion' score/flags and return flagged rows."""
    flags = pd.DataFrame(index=df.index)
    flags["high_value"] = False
    flags["repeated_vendor"] = False
    flags["missing_id"] = False

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

    flags["suspicious"] = flags.any(axis=1)
    out = df.copy()
    out = out.assign(**flags)
    return out[out["suspicious"]]

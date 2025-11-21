import pandas as pd
from typing import Dict, Any


def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    kpis = {}
    kpis["total_contracts"] = int(len(df))
    if "contract_amount" in df.columns:
        total = float(df["contract_amount"].dropna().sum())
        kpis["total_value"] = total
        kpis["average_value"] = float(df["contract_amount"].dropna().mean() or 0)
        kpis["median_value"] = float(df["contract_amount"].dropna().median() or 0)
    else:
        kpis["total_value"] = 0.0
        kpis["average_value"] = 0.0
        kpis["median_value"] = 0.0

    # Top vendors by contract amount
    if "vendor" in df.columns:
        top_vendors = (
            df.groupby("vendor", dropna=True)["contract_amount"].sum().sort_values(ascending=False).head(10)
        )
        kpis["top_vendors"] = top_vendors
    else:
        kpis["top_vendors"] = pd.Series([], dtype=float)

    # Contracts by status
    if "status" in df.columns:
        kpis["by_status"] = df["status"].value_counts()
    else:
        kpis["by_status"] = pd.Series([], dtype=int)

    return kpis


def contracts_over_time(df: pd.DataFrame, date_col: str = "contractDate", freq: str = "M") -> pd.Series:
    if date_col not in df.columns:
        return pd.Series([], dtype=float)
    s = df.set_index(pd.to_datetime(df[date_col], errors="coerce"))["contract_amount"].dropna()
    return s.resample(freq).count().fillna(0)

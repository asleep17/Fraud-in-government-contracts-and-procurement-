import pandas as pd
import plotly.express as px


def contracts_over_time_figure(df: pd.DataFrame, date_col: str = "contractDate"):
    if date_col not in df.columns:
        return None
    dates = pd.to_datetime(df[date_col], errors="coerce")
    ts = df.assign(contract_date=dates).dropna(subset=["contract_date"]).groupby(pd.Grouper(key="contract_date", freq="M")).size().reset_index(name="count")
    fig = px.line(ts, x="contract_date", y="count", title="Contracts Over Time")
    fig.update_xaxes(title="Date")
    fig.update_yaxes(title="Number of Contracts")
    return fig


def top_vendors_figure(df: pd.DataFrame, vendor_col: str = "vendor", n: int = 10):
    if vendor_col not in df.columns:
        return None
    grp = df.groupby(vendor_col)["contract_amount"].sum().sort_values(ascending=False).head(n).reset_index()
    fig = px.bar(grp, x="contract_amount", y=vendor_col, orientation="h", title=f"Top {n} Vendors by Contract Value")
    return fig


def procurement_method_pie(df: pd.DataFrame, method_col: str = "procurement_method"):
    if method_col not in df.columns:
        return None
    pc = df[method_col].value_counts().reset_index()
    pc.columns = [method_col, "count"]
    fig = px.pie(pc, names=method_col, values="count", title="Procurement Methods")
    return fig

import math
from typing import Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from features import fraud_checks
from features.visuals import contracts_over_time_figure
from utils.data_loader import load_data

st.set_page_config(page_title="Fraud & Procurement Risk Dashboard", layout="wide", initial_sidebar_state="expanded")

DATASET_OPTIONS = {
    "Synthetic mock dataset (fraud-ready)": "mock_data.csv",
    "Combined scraped dataset": "combined_contract_data.csv",
}

CATEGORY_CANDIDATES = ["procurement_category", "procurement_method"]
ENTITY_CANDIDATES = ["publicEntityName", "publicEntity", "pe_name"]


@st.cache_data(show_spinner=False)
def load_cached_dataset(path: str) -> pd.DataFrame:
    return load_data(path)


def load_selected_dataset(selection: str, uploaded_file) -> Tuple[pd.DataFrame, str]:
    if uploaded_file is not None:
        return load_data(uploaded_file), "Uploaded CSV"
    path = DATASET_OPTIONS.get(selection, "mock_data.csv")
    return load_cached_dataset(path), path


def detect_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def calculate_dashboard_data(data: pd.DataFrame, category_col: Optional[str], entity_col: Optional[str]):
    metrics = {
        "total_contracts": int(len(data)),
        "total_value": float(data["contract_amount"].sum()) if "contract_amount" in data else 0.0,
        "avg_value": float(data["contract_amount"].mean()) if "contract_amount" in data else 0.0,
    }

    if "status" in data.columns:
        status_counts = data["status"].value_counts(dropna=False).reset_index()
        status_counts.columns = ["status", "count"]
        metrics["status_data"] = status_counts
        completed = data[data["status"].str.lower() == "completed"] if not data.empty else pd.DataFrame()
        metrics["completion_rate"] = (
            len(completed) / len(data) * 100 if len(data) else 0.0
        )
    else:
        metrics["status_data"] = pd.DataFrame(columns=["status", "count"])
        metrics["completion_rate"] = 0.0

    if category_col:
        cat_counts = data[category_col].fillna("Unknown").value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        metrics["category_data"] = cat_counts
    else:
        metrics["category_data"] = pd.DataFrame(columns=["category", "count"])

    if entity_col and "contract_amount" in data.columns:
        entity_data = (
            data.groupby(entity_col)["contract_amount"]
            .sum()
            .reset_index()
            .sort_values(by="contract_amount", ascending=False)
            .head(5)
        )
        entity_data.columns = ["entity", "total_value"]
        metrics["entity_data"] = entity_data
    else:
        metrics["entity_data"] = pd.DataFrame(columns=["entity", "total_value"])

    return metrics


def format_currency(value: float) -> str:
    if value >= 1_000_000:
        return f"NPR {value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"NPR {value/1_000:.1f}K"
    return f"NPR {value:,.0f}"


st.title("🏛️ Fraud & Procurement Risk Dashboard")
st.caption("Analyze procurement data with rule-based fraud checks powered by the mock dataset.")

sidebar = st.sidebar
sidebar.header("Filters")

dataset_choice = sidebar.selectbox("Dataset", list(DATASET_OPTIONS.keys()), index=0)
uploaded = sidebar.file_uploader("Upload CSV (optional)", type=["csv"])

df_raw, data_label = load_selected_dataset(dataset_choice, uploaded)
scored_df = fraud_checks.score_risk(df_raw)

status_values = (
    sorted(scored_df["status"].dropna().unique()) if "status" in scored_df.columns else []
)
risk_levels = ["Critical", "High", "Medium", "Low"]
max_score_value = (
    scored_df["risk_score"].max() if "risk_score" in scored_df.columns else float("nan")
)
if pd.isna(max_score_value):
    max_score_value = 0
max_score = max(100, int(math.ceil(max_score_value)))

status_filter = sidebar.multiselect("Status", status_values, default=status_values)
risk_filter = sidebar.multiselect("Risk levels", risk_levels, default=risk_levels)
score_range = sidebar.slider("Risk score range", 0, max_score, (0, max_score))

filtered = scored_df.copy()
if status_values and status_filter:
    filtered = filtered[filtered["status"].isin(status_filter)]
if risk_filter:
    filtered = filtered[filtered["risk_level"].isin(risk_filter)]
filtered = filtered[
    (filtered["risk_score"] >= score_range[0]) & (filtered["risk_score"] <= score_range[1])
] if "risk_score" in filtered.columns else filtered

active_count = len(filtered)

category_column = detect_column(filtered, CATEGORY_CANDIDATES)
entity_column = detect_column(filtered, ENTITY_CANDIDATES)
metrics = calculate_dashboard_data(filtered, category_column, entity_column)

overview_tab, fraud_tab, data_tab = st.tabs(
    ["Portfolio Overview", "Fraud Risk Model", "Data Explorer"]
)

with overview_tab:
    st.subheader("Key Performance Indicators")
    if active_count == 0:
        st.info("No contracts match the current filters.")
    else:
        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Contracts", metrics["total_contracts"])
        kpi_cols[1].metric("Total Value", format_currency(metrics["total_value"]))
        kpi_cols[2].metric("Average Value", format_currency(metrics["avg_value"]))
        kpi_cols[3].metric("Completion Rate", f"{metrics['completion_rate']:.1f}%")

        chart_col1, chart_col2 = st.columns([1, 1])
        if not metrics["status_data"].empty:
            with chart_col1:
                st.markdown("**Status Distribution**")
                status_fig = px.pie(
                    metrics["status_data"],
                    values="count",
                    names="status",
                    hole=0.35,
                    color="status",
                )
                status_fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(status_fig, use_container_width=True)
        if not metrics["category_data"].empty:
            with chart_col2:
                st.markdown("**Procurement Mix**")
                category_fig = px.bar(
                    metrics["category_data"],
                    x="category",
                    y="count",
                    color="category",
                    labels={"category": category_column or "procurement_method"},
                )
                category_fig.update_layout(showlegend=False)
                st.plotly_chart(category_fig, use_container_width=True)

        if not metrics["entity_data"].empty:
            st.markdown("**Top Entities by Contract Value**")
            entity_fig = px.bar(
                metrics["entity_data"],
                x="total_value",
                y="entity",
                orientation="h",
                labels={"total_value": "Total Value (NPR)", "entity": "Entity"},
            )
            st.plotly_chart(entity_fig, use_container_width=True)

        time_fig = contracts_over_time_figure(filtered)
        if time_fig:
            time_fig.update_layout(
                height=220,
                showlegend=False,
                margin=dict(t=20, b=0, l=10, r=10),
            )
            time_fig.update_xaxes(title="", showgrid=False)
            time_fig.update_yaxes(title="", showgrid=False)
            st.markdown("**Status Trend (sparkline)**")
            st.plotly_chart(time_fig, use_container_width=True)

with fraud_tab:
    st.subheader("Rule-Based Fraud Model Snapshot")
    if active_count == 0:
        st.info("No contracts available to score under the current filters.")
    else:
        risk_counts = filtered["risk_level"].value_counts().reindex(risk_levels, fill_value=0)
        risk_cols = st.columns(4)
        for label, col in zip(risk_levels, risk_cols):
            col.metric(f"{label} risk", int(risk_counts[label]))

        hist_fig = px.histogram(
            filtered,
            x="risk_score",
            color="risk_level",
            nbins=20,
            labels={"risk_score": "Risk Score"},
        )
        hist_fig.update_layout(bargap=0.05)
        st.plotly_chart(hist_fig, use_container_width=True)

        if {"cost_variance_pct", "payment_discrepancy"}.issubset(filtered.columns):
            scatter_data = filtered.dropna(subset=["cost_variance_pct", "payment_discrepancy"])
            if not scatter_data.empty:
                hover_fields = []
                if "contract_id" in scatter_data.columns:
                    hover_fields.append("contract_id")
                elif "contract_code" in scatter_data.columns:
                    hover_fields.append("contract_code")
                if "contract_name" in scatter_data.columns:
                    hover_fields.append("contract_name")
                elif "vendor" in scatter_data.columns:
                    hover_fields.append("vendor")
                if "risk_reasons" in scatter_data.columns:
                    hover_fields.append("risk_reasons")

                scatter_kwargs = dict(
                    data_frame=scatter_data,
                    x="cost_variance_pct",
                    y="payment_discrepancy",
                    color="risk_level",
                    hover_data=hover_fields,
                    labels={
                        "cost_variance_pct": "Cost Variance (%)",
                        "payment_discrepancy": "Payment Discrepancy (NPR)",
                    },
                )
                if "contract_amount" in scatter_data.columns:
                    scatter_kwargs["size"] = "contract_amount"

                scatter_fig = px.scatter(**scatter_kwargs)
                st.plotly_chart(scatter_fig, use_container_width=True)

        st.markdown("**Highest-Risk Contracts**")
        risk_view = filtered.sort_values(by="risk_score", ascending=False)
        display_cols = [
            col
            for col in [
                "contract_id",
                "contract_name",
                "publicEntityName",
                "contract_amount",
                "procurement_method",
                "status",
                "risk_level",
                "risk_score",
                "risk_reasons",
            ]
            if col in risk_view.columns
        ]
        st.dataframe(risk_view[display_cols].head(25), use_container_width=True)
        csv_export = risk_view.to_csv(index=False).encode("utf-8")
        st.download_button("Download scored contracts (CSV)", csv_export, "fraud_scores.csv", "text/csv")

        st.caption(
            "The fraud model assigns higher scores to contracts with limited competition, abnormal cost or payment patterns, "
            "delayed delivery, and associations with red-flagged or blacklisted entities."
        )

with data_tab:
    st.subheader("Filtered dataset")
    st.dataframe(filtered, use_container_width=True, height=400)
    st.caption(f"Source: {data_label}")
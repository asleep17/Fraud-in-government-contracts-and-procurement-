import streamlit as st
import pandas as pd
from utils.data_loader import load_data
from features import overview, visuals, fraud_checks


@st.cache_data
def _load(path: str = "combined_contract_data.csv") -> pd.DataFrame:
	return load_data(path)


def show_overview(df: pd.DataFrame):
	kpis = overview.compute_kpis(df)
	st.title("Government Contracts — Overview")
	cols = st.columns(3)
	cols[0].metric("Total Contracts", f"{kpis['total_contracts']}")
	cols[1].metric("Total Value", f"{kpis['total_value']:,.0f}")
	cols[2].metric("Average Value", f"{kpis['average_value']:,.0f}")

	st.subheader("Contracts by Status")
	st.bar_chart(kpis['by_status'])

	st.subheader("Top Vendors")
	if not kpis['top_vendors'].empty:
		st.dataframe(kpis['top_vendors'].rename_axis('vendor').reset_index().rename(columns={'contract_amount':'total_value'}))


def show_visuals(df: pd.DataFrame):
	st.title("Visualizations")
	fig = visuals.contracts_over_time_figure(df)
	if fig:
		st.plotly_chart(fig, use_container_width=True)

	fig2 = visuals.top_vendors_figure(df)
	if fig2:
		st.plotly_chart(fig2, use_container_width=True)

	fig3 = visuals.procurement_method_pie(df)
	if fig3:
		st.plotly_chart(fig3, use_container_width=True)


def show_fraud_checks(df: pd.DataFrame):
	st.title("Fraud Checks & Heuristics")
	st.write("Simple heuristic flags — review results manually.")

	high = fraud_checks.flag_high_value(df)
	st.subheader("High-value contracts (top 1%)")
	st.dataframe(high)

	repeated = fraud_checks.flag_repeated_vendors(df)
	st.subheader("Vendors with many contracts")
	st.dataframe(repeated)

	missing = fraud_checks.flag_missing_ids(df)
	st.subheader("Contracts with missing identifiers")
	st.dataframe(missing)

	combined = fraud_checks.combined_suspicion(df)
	st.subheader("Combined suspicious rows")
	st.dataframe(combined)


def main():
	st.sidebar.title("Navigation")
	page = st.sidebar.radio("Go to", ["Overview", "Visuals", "Fraud Checks", "Data Table"]) 

	df = _load("combined_contract_data.csv")

	if page == "Overview":
		show_overview(df)
	elif page == "Visuals":
		show_visuals(df)
	elif page == "Fraud Checks":
		show_fraud_checks(df)
	elif page == "Data Table":
		st.title("Raw Data")
		st.dataframe(df)


if __name__ == "__main__":
	main()


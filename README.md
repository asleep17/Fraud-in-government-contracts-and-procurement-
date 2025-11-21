
# Fraud-in-government-contracts-and-procurement-
Fraud in government contracts and procurement  By GenNepal 
<break>
<h5>web app link : https://asleep17-fraud-in-government-contracts-and-procurem-app-yqguzo.streamlit.app
#  Procurement Fraud & Risk Dashboard

This repository contains the code and data used to build an interactive dashboard for detecting and prioritizing potential fraud, waste, and abuse in government procurement contracts.

The primary goal is to shift auditing from manual review to **risk-based prioritization** by automatically scoring contracts based on a set of red flags. 

---

##  Getting Started

To run the dashboard locally, you need Python and the required libraries.

### Prerequisites

1. Clone this repository (or download all files).
2. Install the necessary Python packages using the provided `requirements.txt` file:

    ```bash
    pip install -r requirements.txt
    ```

### Running the Dashboard

Launch the Streamlit application from your terminal:

```bash
streamlit run app.py

Fraud-in-government-contracts-and-procurement/
├── app.py
│   └── Main Streamlit dashboard code.
│       Handles UI layout, filters, visualizations, and risk scores.
│
├── bolpatra_detail_scrape.py
│   └── Web scraping script to collect detailed contract data
│       from the Bolpatra/source procurement system.
│
├── Cleandata.ipynb
│   └── Jupyter Notebook for data cleaning, transformation,
│       schema fixing, and merging scraped datasets.
│
├── data/
│   ├── mock_data.csv
│   │   └── Synthetic sample dataset for demo/testing fraud checks.
│   │
│   ├── combined_contract_data.csv
│   │   └── Final merged + cleaned dataset used by the dashboard.
│   │
│   ├── contracts.csv
│   │   └── Raw/intermediate scraped contracts file.
│   │
│   └── contract_details.csv
│       └── Raw/intermediate detailed contracts file from scraping.
│
├── requirements.txt
│   └── Python dependencies (streamlit, pandas, plotly, numpy, etc.).
│
├── LICENSE
│   └── MIT License for the project.
│
└── README.md
    └── Project documentation and setup guide.

 Key Solutions
The dashboard provides a solution by focusing on Detection, Prioritization, and Transparency:

Risk Scoring: Every contract is given a numerical risk_score based on rules (e.g., low bidder count, high cost variance) to instantly rank and prioritize investigation targets.

Risk Explanation: The model provides explicit risk_reasons for each score, offering an immediate audit trail and justification for action.

Systemic Analysis: Charts help identify systemic risks, such as over-reliance on limited competition or vendor market capture, rather than just isolated fraud cases.
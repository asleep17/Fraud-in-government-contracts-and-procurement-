import requests
import urllib3
import csv
from bs4 import BeautifulSoup
import pandas

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --------------------------
# CONSTANTS
# --------------------------
DETAIL_URL = "https://bolpatra.gov.np/egp/loadViewContractRecordsPublic"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://bolpatra.gov.np/egp/loadContractRecordsListPublic",
}




# --------------------------
# POST REQUEST TO GET DETAILS
# --------------------------
def fetch_contract_detail(session, contract_id):
    """
    IMPORTANT:
    Bolpatra requires EXACT payload key:
        contractRecordsTO.contractId = <contract_code>
    """
    payload = {
        "contractRecordsTO.contractId": contract_id
    }

    response = session.post(
        DETAIL_URL,
        data=payload,
        headers=HEADERS,
        verify=False,
        timeout=20,
    )

    # Handle server error (500)
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: Could not fetch {contract_id}")

    return response.text


# --------------------------
# PARSE CONTRACT PAGE
# --------------------------
def parse_contract_page(html):
    soup = BeautifulSoup(html, "lxml")
    data = {}

    # Extract the entire form fields
    inputs = soup.find_all("input")
    selects = soup.find_all("select")
    textareas = soup.find_all("textarea")

    # INPUT fields
    for inp in inputs:
        name = inp.get("name")
        value = inp.get("value", "").strip()
        if name and value:
            data[name] = value

    # SELECT fields
    for sel in selects:
        name = sel.get("name")
        selected_option = sel.find("option", selected=True)
        if name and selected_option:
            data[name] = selected_option.text.strip()

    # TEXTAREAS
    for ta in textareas:
        name = ta.get("name")
        value = ta.text.strip()
        if name:
            data[name] = value

    return data


# --------------------------
# MAIN SCRAPER
# --------------------------
def main():
    contract_ids = pandas.read_csv("contracts.csv")
    print(f"🔍 Found {contract_ids.shape[0]} contract IDs")

    session = requests.Session()
    results = []

    for i, cid in enumerate(contract_ids["contract_code"], start=1):
        print(f"[{i}/{contract_ids.shape[0]}] Fetching {cid} ...")

        try:
            html = fetch_contract_detail(session, cid)
            parsed = parse_contract_page(html)
            parsed["contract_id"] = cid
            results.append(parsed)


        except Exception as error:
            print(f"❌ ERROR for {cid}: {error}")


    # --------------------------
    # WRITE TO CSV
    # --------------------------
    if not results:
        print("No data extracted. Something went wrong.")
        return

    # Collect every key from all records
    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    all_keys = sorted(list(all_keys))

    with open("contract_details.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print("\n✅ DONE! Saved to contract_details.csv")


if __name__ == "__main__":
    main()

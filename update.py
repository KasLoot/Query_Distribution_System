import requests
import json
import os

# ======================
# Config
# ======================
APP_ID = "cli_a98cd34bba38de1a"
APP_SECRET = "gBjwBVIwsVwK8mgRXWB1LcSCyxkn7P4S"
SHEET_TOKEN = "EzezsDebzhSvL8tHkKIjjUU1p6f"
SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "calendar/schedule.json")


def lark_update_done():
    # 1️⃣ Get tenant access token
    res = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
    )
    res.raise_for_status()
    token = res.json()["tenant_access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Got token")

    # 2️⃣ Get sheet metadata
    res_meta = requests.get(
        f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/metainfo",
        headers=headers,
    )
    res_meta.raise_for_status()
    meta_data = res_meta.json()["data"]["sheets"][0]
    sheet_name = meta_data["title"]
    sheet_id = meta_data["sheetId"]
    print(f"✅ Sheet name: {sheet_name}, ID: {sheet_id}")

    # 3️⃣ Load local JSON
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        local_data = json.load(f)

    # 4️⃣ Read existing rows (A:F)
    url_read = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values/{sheet_id}!A:F"
    res_read = requests.get(url_read, headers=headers)
    print("📡 Read status:", res_read.status_code)
    res_read.raise_for_status()
    raw = res_read.json()
    print("📜 Response snippet:", json.dumps(raw)[:300])

    data_json = raw.get("data", {})
    if "valueRange" in data_json:
        sheet_values = data_json["valueRange"].get("values", [])
    elif "values" in data_json:
        sheet_values = data_json["values"]
    else:
        raise ValueError("❌ Unexpected API response structure")

    print(f"✅ Loaded {len(sheet_values)} rows from sheet")

    # 5️⃣ Update “DONE?” column (column F)
    for person, tasks in local_data.items():
        for task in tasks:
            title = task.get("title")
            done = task.get("done", False)

            for i, row in enumerate(sheet_values[1:], start=2):
                if len(row) >= 4 and row[0] == title and row[3] == person:
                    value = "✅ Done" if done else ""
                    range_str = f"{sheet_id}!F{i}:F{i}"
                    url_put = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values"
                    payload = {
                        "valueRange": {
                            "range": range_str,
                            "values": [[value]],
                        }
                    }

                    res_put = requests.put(url_put, headers=headers, json=payload)
                    print(f"🔄 Updating Row {i} ({title} - {person}):", res_put.status_code, res_put.text)

    print("✅ All updates attempted!")


if __name__ == "__main__":
    lark_update_done()
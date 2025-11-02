from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, requests, threading

app = Flask(__name__)
CORS(app)

# ======================
# Config
# ======================
SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "schedule.json")
APP_ID = "cli_a98cd34bba38de1a"
APP_SECRET = "gBjwBVIwsVwK8mgRXWB1LcSCyxkn7P4S"
SHEET_TOKEN = "EzezsDebzhSvL8tHkKIjjUU1p6f"  # spreadsheet token from Lark URL


# ======================
# Lark API Helpers
# ======================
def get_lark_token():
    """Get Tenant Access Token"""
    res = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
    )
    res.raise_for_status()
    token = res.json()["tenant_access_token"]
    print("✅ 取得 Lark Token 成功")
    return token


def get_sheet_meta(token):
    """Get sheet_id and sheet_name"""
    headers = {"Authorization": f"Bearer {token}"}
    url_meta = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/metainfo"
    res_meta = requests.get(url_meta, headers=headers)
    res_meta.raise_for_status()
    data = res_meta.json()["data"]["sheets"][0]
    sheet_name = data["title"]
    sheet_id = data["sheetId"]
    print(f"✅ Sheet name: {sheet_name}, ID: {sheet_id}")
    return sheet_id, sheet_name


def read_lark_data(token, sheet_id):
    """✅ Read sheet content via Lark API v3 (correct endpoint)"""
    headers = {"Authorization": f"Bearer {token}"}
    url_read = f"https://open.larksuite.com/open-apis/sheets/v3/spreadsheets/{SHEET_TOKEN}/sheets/{sheet_id}/values_batch_get"
    payload = {"ranges": ["A:E"]}
    res = requests.post(url_read, headers=headers, json=payload)
    print("📡 Read request sent:", res.status_code)
    print("📜 Response text:", res.text)
    res.raise_for_status()

    data = res.json()
    values = data["data"]["valueRanges"][0]["values"]
    print(f"✅ 讀取 Lark Sheet 成功，共 {len(values)} 行")
    return values


def update_lark_cells(token, sheet_id, updates):
    """✅ Append or update Lark cells using v2/values_append (proven working)"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url_append = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values_append"

    # build payloads same as your working code
    payload = {
        "valueRange": {
            "range": f"{sheet_id}!A:E",
            "values": [[u.get("query"), u.get("est_time", ""), u.get("priority", ""), u.get("person", ""), u.get("status", "")] for u in updates]
        }
    }

    res = requests.post(url_append, headers=headers, json=payload)
    print("📡 Lark append request:", res.status_code)
    print("📜 Response:", res.text)

    if res.status_code == 200 and res.json().get("code") == 0:
        print("✅ Appended successfully to Lark!")
    else:
        print("❌ Append failed:", res.json())


# ======================
# Core Sync Logic
# ======================
def sync_json_to_lark():
    """Sync done/undone status from schedule.json → Lark"""
    try:
        # Load local JSON
        with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        token = get_lark_token()
        sheet_id, sheet_name = get_sheet_meta(token)
        sheet_data = read_lark_data(token, sheet_id)

        updates = []
        for person, tasks in data.items():
            for task in tasks:
                title = task.get("title")
                done = task.get("done", False)
                for i, row in enumerate(sheet_data[1:], start=2):
                    if len(row) >= 4 and row[0] == title and row[3] == person:
                        cell_value = "✅ Done" if done else ""
                        updates.append({
                            "range": f"E{i}",
                            "values": [[cell_value]]
                        })

        if updates:
            update_lark_cells(token, sheet_id, updates)
        else:
            print("ℹ️ No matching rows found in Lark.")
    except Exception as e:
        print("❌ Lark sync failed:", e)


# ======================
# Flask Routes
# ======================
@app.route("/get_tasks", methods=["GET"])
def get_tasks():
    """Serve schedule.json"""
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/update_task", methods=["POST"])
def update_task():
    """Update JSON and auto-sync to Lark"""
    try:
        data = request.json
        with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ schedule.json updated by frontend")

        threading.Thread(target=sync_json_to_lark, daemon=True).start()
        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Error saving schedule.json:", e)
        return jsonify({"status": "error"}), 500


if __name__ == "__main__":
    app.run(port=5501, debug=True)
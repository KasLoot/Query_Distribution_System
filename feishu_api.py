import requests
from datetime import datetime
from collections import defaultdict


APP_ID = "cli_a98cd34bba38de1a"
APP_SECRET = "gBjwBVIwsVwK8mgRXWB1LcSCyxkn7P4S"
SHEET_TOKEN = "EzezsDebzhSvL8tHkKIjjUU1p6f"

def lark_writing(query: str, est_time: int, priority: str, person: str):
    res = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    token = res.json()["tenant_access_token"]
    print("Get token successfully !")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


    url_meta = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/metainfo"
    res_meta = requests.get(url_meta, headers=headers)
    meta_data = res_meta.json()["data"]["sheets"][0]

    sheet_name = meta_data["title"]
    sheet_id = meta_data["sheetId"]
    print(f"Page name: {sheet_name}")
    print(f"Page ID: {sheet_id}")

    # Write data
    url_append = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values_append"


    payload = {
        "valueRange": {
            "range": f"{sheet_id}!A:E",  
            "values": [
                [query, est_time, priority, person, datetime.now().isoformat()]
            ]
        }
    }

    res2 = requests.post(url_append, json=payload, headers=headers)
    print("Result：", res2.status_code, res2.json())

    if res2.status_code == 200 and res2.json().get("code") == 0:
        print("Success! Please check the form")
    else:
        print("error：", res2.json())




def lark_read_and_group():
    # Step 1️⃣ 拿 token
    res = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    res.raise_for_status()
    token = res.json()["tenant_access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2️⃣ 拿 sheetId
    meta_url = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/metainfo"
    meta_res = requests.get(meta_url, headers=headers)
    meta_res.raise_for_status()
    meta_data = meta_res.json()["data"]["sheets"][0]
    sheet_id = meta_data["sheetId"]
    sheet_name = meta_data["title"]
    print(f"✅ 表格名稱: {sheet_name}, ID: {sheet_id}")

    # Step 3️⃣ 用 sheetId 讀資料
    range_str = f"{sheet_id}!A:D"
    read_url = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values/{range_str}"
    res_data = requests.get(read_url, headers=headers)
    print("🔍 API 狀態:", res_data.status_code)
    print("🧾 回傳:", res_data.text[:200])
    res_data.raise_for_status()

    result_json = res_data.json()
    values = result_json["data"]["valueRange"]["values"]

    headers_row = values[0]
    rows = [dict(zip(headers_row, row)) for row in values[1:]]

    # Step 4️⃣ 分組
    tasks = defaultdict(list)
    for row in rows:
        person = row.get("PERSON", "Unassigned")
        tasks[person].append({
            "query": row.get("Query", ""),
            "estimated_time": row.get("Estimated time", ""),
            "priority": row.get("Priority", "")
        })

    print("📊 分組結果:", dict(tasks))
    return dict(tasks)







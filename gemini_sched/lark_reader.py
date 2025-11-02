from collections import defaultdict
import requests
import json

APP_ID = "cli_a98cd34bba38de1a"
APP_SECRET = "gBjwBVIwsVwK8mgRXWB1LcSCyxkn7P4S"
SHEET_TOKEN = "EzezsDebzhSvL8tHkKIjjUU1p6f"

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
            "priority": row.get("Priority", ""),
            "person": row.get("PERSON","")
        })
    print(tasks)
    print("📊 分組結果:", dict(tasks))
    to_json = []
    for person, items in tasks.items():
        for item in items:
            task = {
                "query": item["query"],
                "estimate_time": int(item["estimated_time"]),  
                "priority": item["priority"],
                "person": [person]  
            }
            to_json.append(task)
    new_data = {"tasks": to_json}
    with open("./gemini_sched/tasks.json", "w") as f:
        json.dump(new_data, f, indent=2)

    print (new_data)
    return dict(tasks), task



if __name__ == "__main__":
    lark_read_and_group()
    


print("tasks.json file created")


        
import json, datetime

def convert_to_24(time_str):
    """將 AM/PM 時間轉成 24 小時制"""
    time, modifier = time_str.split(" ")
    hours, minutes = time.split(":")
    if modifier == "PM" and hours != "12":
        hours = str(int(hours) + 12)
    if modifier == "AM" and hours == "12":
        hours = "00"
    return f"{hours.zfill(2)}:{minutes}:00"


def update_calendar(gemini_output, save_path="schedule.json"):
    """
    將 Gemini 輸出的任務格式轉換成 FullCalendar 能用的格式，
    並寫入 schedule.json。
    """
    today = datetime.date.today().isoformat()
    formatted = {}

    for staff in gemini_output:
        name = staff["staff_member"]
        formatted[name] = []
        for t in staff["tasks"]:
            formatted[name].append({
                "title": t["task_name"],
                "start": f"{today}T{convert_to_24(t['time_start'])}",
                "end": f"{today}T{convert_to_24(t['time_end'])}",
                "priority": (
                    "High" if t["priority"] == 1
                    else "Medium" if t["priority"] == 2
                    else "Low"
                )
            })

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(formatted, f, ensure_ascii=False, indent=2)

    print(f"✅ 已更新行事曆檔案：{save_path}")
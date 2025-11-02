from google import genai
from google.genai import types
import json, datetime, re

# ==============================
# 🔹 Gemini API Setup
# ==============================
client = genai.Client(api_key="AIzaSyCDqagBpp-Tqi9qtJ2MDQBd_Hpq8gvzQ7I")  # Replace with your actual key

# ==============================
# 🔹 Time Conversion + Calendar Writer
# ==============================
def convert_to_24(time_str):
    """Convert 12-hour AM/PM time to 24-hour format"""
    time, modifier = time_str.split(" ")
    hours, minutes = time.split(":")
    if modifier == "PM" and hours != "12":
        hours = str(int(hours) + 12)
    if modifier == "AM" and hours == "12":
        hours = "00"
    return f"{hours.zfill(2)}:{minutes}:00"


def update_calendar(gemini_output, save_path="./calendar/schedule.json"):
    """
    Convert Gemini's schedule output into FullCalendar format and save to schedule.json
    (Automatically skips weekends)
    """
    # 🔹 找出要用的排程日期（如果今天是週末 → 自動移動到下週一）
    today = datetime.date.today()
    if today.weekday() >= 5:  # 週六 = 5, 週日 = 6
        days_to_monday = 7 - today.weekday()
        today = today + datetime.timedelta(days=days_to_monday)
    today_str = today.isoformat()

    formatted = {}

    for staff in gemini_output:
        name = staff["staff_member"]
        formatted[name] = []

        for t in staff["tasks"]:
            formatted[name].append({
                "title": t["task_name"],
                "start": f"{today_str}T{convert_to_24(t['time_start'])}",
                "end": f"{today_str}T{convert_to_24(t['time_end'])}",
                "priority": t["priority"],
                "notes": t.get("notes", "")
            })

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(formatted, f, ensure_ascii=False, indent=2)

    print(f"✅ Calendar updated successfully for {today.strftime('%A')} ({today_str}) → {save_path}")

def plan():
    # ==============================
    # 🔹 Gemini Function Schema
    # ==============================
    schedule_function = {
        "name": "schedule",
        "description": "Arrange each staff member's daily schedule with task priority and time slots.",
        "parameters": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "staff_member": {"type": "string"},
                            "total_task_hours": {"type": "number"},
                            "tasks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "time_start": {"type": "string"},
                                        "time_end": {"type": "string"},
                                        "duration_hours": {"type": "number"},
                                        "task_name": {"type": "string"},
                                        "priority": {"type": "integer"},
                                        "notes": {"type": "string"}
                                    },
                                    "required": ["time_start", "time_end", "task_name", "priority"]
                                }
                            }
                        },
                        "required": ["staff_member", "tasks"]
                    }
                }
            },
            "required": ["tasks"]
        }
    }

    tools = types.Tool(function_declarations=[schedule_function])
    config = types.GenerateContentConfig(tools=[tools])


    # ==============================
    # 🔹 Function Gemini Calls
    # ==============================
    def schedule(tasks):
        print("📅 Gemini triggered schedule() ...")
        update_calendar(tasks)
        print("✅ schedule.json successfully updated!")


    # ==============================
    # 🔹 Load Task Data
    # ==============================
    with open("./gemini_sched/tasks.json", "r") as f:
        task_data = json.load(f)

    with open("./gemini_sched/schedule_system.txt", "r") as f:
        system_prompt = f.read()

    prompt = system_prompt + f"""
    Task data:
    {json.dumps(task_data, indent=2, ensure_ascii=False)}
    """

    # ==============================
    # 🔹 Call Gemini Model
    # ==============================
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=config,
    )

    # ==============================
    # 🔹 Handle Gemini Function or JSON Output
    # ==============================
    try:
        # --- 若模型有觸發 function call ---
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
            and hasattr(response.candidates[0].content.parts[0], "function_call")
            and response.candidates[0].content.parts[0].function_call
        ):
            fn = response.candidates[0].content.parts[0].function_call
            print(f"\nGemini called function: {fn.name}")
            print(f"Arguments: {json.dumps(fn.args, indent=2, ensure_ascii=False)}")
            if fn.name == "schedule":
                args = fn.args
                schedule(tasks=args["tasks"])

        else:
            # --- 沒 function call → 嘗試自動抽出 JSON ---
            print("⚠️ 沒有偵測到 function call，改嘗試解析 JSON 輸出。")

            text_output = response.text.strip()
            # 移除 markdown code block 包裝
            if text_output.startswith("```"):
                matches = re.findall(r"```json(.*?)```", text_output, re.DOTALL)
                if matches:
                    text_output = matches[0]
                else:
                    text_output = text_output.replace("```json", "").replace("```", "").strip()

            # 找出第一個合法 JSON（忽略後面說明文字）
            json_match = re.search(r"\{[\s\S]*\}", text_output)
            if not json_match:
                raise ValueError("❌ 無法在輸出中找到 JSON 結構。")

            json_text = json_match.group(0)
            json_data = json.loads(json_text)

            # 根據輸出結構選擇正確欄位
            if "staff_schedules" in json_data:
                update_calendar(json_data["staff_schedules"])
            elif "tasks" in json_data:
                update_calendar(json_data["tasks"])
            else:
                update_calendar(json_data)

            print("✅ schedule.json 已成功更新（fallback 模式）")

    except Exception as e:
        print("❌ Error processing response:", e)
        print(response)

if __name__ == "__main__":
    plan()
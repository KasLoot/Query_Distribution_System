from google import genai
from google.genai import types
import json, datetime

# ==============================
# 🔹 Gemini API Setup
# ==============================
client = genai.Client(api_key="AIzaSyCDqagBpp-Tqi9qtJ2MDQBd_Hpq8gvzQ7I")  # ← Replace with your real key


# ==============================
# 🔹 Time Conversion + Calendar Writer
# ==============================
def convert_to_24(time_str):
    """Convert 12-hour time format (AM/PM) to 24-hour time"""
    time, modifier = time_str.split(" ")
    hours, minutes = time.split(":")
    if modifier.upper() == "PM" and hours != "12":
        hours = str(int(hours) + 12)
    if modifier.upper() == "AM" and hours == "12":
        hours = "00"
    return f"{hours.zfill(2)}:{minutes}:00"


# def update_calendar(gemini_output, save_path="./calendar/schedule.json"):
#     """
#     Convert Gemini's schedule output into FullCalendar format and save to schedule.json
#     """
#     today = datetime.date.today().isoformat()
#     formatted = {}

#     for staff in gemini_output:
#         name = staff["staff_member"]
#         formatted[name] = []
#         for t in staff["tasks"]:
#             formatted[name].append({
#                 "title": t["task_name"],
#                 "start": f"{today}T{convert_to_24(t['time_start'])}",
#                 "end": f"{today}T{convert_to_24(t['time_end'])}",
#                 "priority": t["priority"],
#                 "notes": t.get("notes", "")
#             })

#     with open(save_path, "w", encoding="utf-8") as f:
#         json.dump(formatted, f, ensure_ascii=False, indent=2)

#     print(f"✅ Calendar updated successfully: {save_path}")


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

# ==============================
# 🔹 Gemini Function Declaration (Schema)
# ==============================
schedule_function = {
    "name": "schedule",
    "description": "Arrange each staff member's daily schedule, considering task priority and urgency.",
    "parameters": {
        "type": "object",  # Gemini requires top-level type=object
        "properties": {
            "tasks": {
                "type": "array",
                "description": "List of staff schedule data",
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
with open("tasks.json", "r") as file:
    data = json.load(file)
data_summary = json.dumps(data, indent=2)

with open("./calendar/schedule.json", "r") as file:
    old_data = json.load(file)
old_data_summary = json.dumps(old_data, indent=2)

with open("schedule_system.txt", "r") as f:
    system_prompt = f.read()

prompt = (
    system_prompt
    + "\n\nHere is the task data from the previous agent in JSON format:\n"
    + data_summary
    + "\n\nAs well as the tasks not done in the previous day:\n"
    + old_data_summary
    + "\n\nNow, arrange the schedule for each staff member considering the priority and urgency."
    + " Directly call the function `schedule()` and pass the JSON above as its argument."
)


# ==============================
# 🔹 Call Gemini Model
# ==============================
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
    config=config,
)


# ==============================
# 🔹 Handle Gemini Function Call
# ==============================
try:
    candidate = response.candidates[0]

    if not candidate or not candidate.content or not candidate.content.parts:
        print("⚠️ No content parts returned.")
    else:
        part = candidate.content.parts[0]

        if getattr(part, "function_call", None):
            fn = part.function_call
            print(f"\n🔧 Gemini called function: {fn.name}")
            print(f"🧩 Arguments: {json.dumps(fn.args, indent=2, ensure_ascii=False)}")

            if fn.name == "schedule":
                # ✅ The schema now wraps tasks inside { "tasks": [...] }
                schedule(tasks=fn.args["tasks"])
        else:
            print("⚠️ No function call detected. Gemini output:")
            print(candidate.content.parts)

except Exception as e:
    print("❌ Error processing response:", e)
    print(response)

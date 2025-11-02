from google import genai
from google.genai import types
import json, datetime

# ==============================
# 🔹 Gemini API Setup
# ==============================
client = genai.Client(api_key="AIzaSyCDqagBpp-Tqi9qtJ2MDQBd_Hpq8gvzQ7I")  # Replace with your actual key


# ==============================
# 🔹 Time Conversion + Calendar Writer
# ==============================
def convert_to_24(time_str):
    """Convert 12-hour time format (AM/PM) to 24-hour time"""
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
                ),
                "notes": t.get("notes", "")
            })

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(formatted, f, ensure_ascii=False, indent=2)

    print(f"✅ Calendar updated successfully: {save_path}")


# ==============================
# 🔹 Gemini Function Declaration (Schema)
# ==============================
schedule_function = {
    "name": "schedule",
    "description": "Arrange each staff member's daily schedule, considering task priority and urgency.",
    "parameters": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "description": "The schedule output for each staff member",
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
                                "required": [
                                    "time_start",
                                    "time_end",
                                    "task_name",
                                    "priority"
                                ]
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
# 🔹 Function that Gemini Calls
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

prompt = f"""
You are an AI scheduling assistant.

Steps:
1️⃣ Based on the following task data, create a structured daily schedule for each employee.
2️⃣ Each staff member’s output should follow this format:
{{
  "staff_member": "Employee name",
  "total_task_hours": float,
  "tasks": [
    {{
      "time_start": "09:00 AM",
      "time_end": "11:00 AM",
      "duration_hours": 2.0,
      "task_name": "Task title",
      "priority": 1,
      "notes": "Short description"
    }},
    ...
  ]
}}
3️⃣ After finishing, **do not output text.**
Directly call the function `schedule()` and pass the JSON above as its argument.

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
# 🔹 Handle Gemini Function Call
# ==============================
try:
    part = response.candidates[0].content.parts[0]
    if hasattr(part, "function_call") and part.function_call:
        fn = part.function_call
        print(f"\n🔧 Gemini called function: {fn.name}")
        print(f"🧩 Arguments: {json.dumps(fn.args, indent=2, ensure_ascii=False)}")

        if fn.name == "schedule":
            args = fn.args
            schedule(tasks=args["tasks"])
    else:
        print("⚠️ No function call detected. Gemini output:")
        print(response.text)

except Exception as e:
    print("❌ Error processing response:", e)
    print(response)
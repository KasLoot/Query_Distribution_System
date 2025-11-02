import json, datetime

def convert_to_24(time_str):
    time, modifier = time_str.split(" ")
    hours, minutes = time.split(":")
    if modifier == "PM" and hours != "12":
        hours = str(int(hours) + 12)
    if modifier == "AM" and hours == "12":
        hours = "00"
    return f"{hours.zfill(2)}:{minutes}:00"

today = datetime.date.today().isoformat()

with open('tasks.json', 'r') as file:
    data = json.load(file)

data_summary = json.dumps(data, indent=2)

for person in gemini_output:
    for t in person["tasks"]:
        t["start"] = f"{today}T{convert_to_24(t['time_start'])}"
        t["end"] = f"{today}T{convert_to_24(t['time_end'])}"

#save to file
with open("schedule.json", "w", encoding="utf-8") as f:
    json.dump(gemini_output, f, ensure_ascii=False, indent=2)

print("✅ Schedule saved to schedule.json")
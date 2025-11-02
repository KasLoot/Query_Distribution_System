from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os

app = Flask(__name__)
CORS(app)

# ======================
# Config
# ======================
SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "schedule.json")


# ======================
# JSON Helpers
# ======================
def load_schedule():
    """Load schedule.json"""
    if not os.path.exists(SCHEDULE_PATH):
        print("⚠️ schedule.json not found — creating a new one.")
        return {}
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule(data):
    """Save schedule.json"""
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ schedule.json saved successfully!")


# ======================
# Flask Routes
# ======================
@app.route("/get_tasks", methods=["GET"])
def get_tasks():
    """Return current schedule.json"""
    data = load_schedule()
    return jsonify(data)


@app.route("/update_task", methods=["POST"])
def update_task():
    """Receive updated JSON and overwrite schedule.json"""
    try:
        new_data = request.json
        save_schedule(new_data)
        print("✅ schedule.json updated via API")
        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Failed to update schedule.json:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/update_single", methods=["POST"])
def update_single():
    """Update a single task (simpler route for frontend)"""
    try:
        data = request.json
        person = data.get("person")
        title = data.get("title")
        done = data.get("done", False)

        schedule = load_schedule()
        if person not in schedule:
            return jsonify({"status": "error", "message": f"Person '{person}' not found"}), 404

        updated = False
        for task in schedule[person]:
            if task.get("title") == title:
                task["done"] = done
                updated = True
                print(f"🔄 Updated: {person} - '{title}' → {'✅ Done' if done else '❌ Not Done'}")
                break

        if not updated:
            return jsonify({"status": "error", "message": f"Task '{title}' not found"}), 404

        save_schedule(schedule)
        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Error in /update_single:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ======================
# Run Server
# ======================
if __name__ == "__main__":
    app.run(port=5501, debug=True)
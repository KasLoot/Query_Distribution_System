#api key AIzaSyCDqagBpp-Tqi9qtJ2MDQBd_Hpq8gvzQ7I

from google import genai
from google.genai import types
import json

# Define the function declaration for the model
schedule_function = {
    "name": "schedule",
    "description": "Arrange schedule for each staff member for their tasks with considering the priority and urgency of each tasks.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The incoming query to be assigned."
            },
            "estimate_time": {
                "type": "integer",
                "description": "The estimate time of the task."
            },
            "priority": {
                "type": "integer",
                "description": "The priority of the task."
            },
            "person": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The staff members to whom the query is assigned."
            },
        },
        "required": ["query", "estimate_time","priority", "person"]
    }
}

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key="AIzaSyCDqagBpp-Tqi9qtJ2MDQBd_Hpq8gvzQ7I")
tools = types.Tool(function_declarations=[schedule_function])
config = types.GenerateContentConfig(tools=[tools])


with open('tasks.json', 'r') as file:
    data = json.load(file)

data_summary = json.dumps(data, indent=2)

with open("schedule_system.txt", "r") as f:
    system_prompt = f.read()

prompt = (
    system_prompt
    + "\n\nHere is the task data from the previous agent in JSON format:\n"
    + data_summary
    + "\n\nNow, arrange the schedule for each staff member considering the priority and urgency."
)


# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=config,
)




def schedule(query, estimate_time, priority, person):
    print(f"Scheduling task: {query}")
    print(f"Estimated time: {estimate_time}")
    print(f"Priority: {priority}")
    print(f"Assigned to: {', '.join(person)}")

# 🔹 Handle function call returned by Gemini
try:
    part = response.candidates[0].content.parts[0]
    if hasattr(part, "function_call") and part.function_call:
        function_call = part.function_call
        print(f"\nFunction to call: {function_call.name}")
        print(f"Arguments: {function_call.args}")

        if function_call.name == "schedule":
            args = function_call.args
            schedule(
                query=args["query"],
                estimate_time=args["estimate_time"],
                priority=args["priority"],
                person=args["person"],
            )
    else:
        print("\n No function call found. Model said:")
        print(response.text)
except Exception as e:
    print(f"Error processing response: {e}")
    print(response)






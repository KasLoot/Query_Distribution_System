from google import genai
from google.genai import types

# Define the function declaration for the model
schedule_meeting_function = {
    "name": "schedule_meeting",
    "description": "Schedules a meeting with specified attendees at a given time and date.",
    "parameters": {
        "type": "object",
        "properties": {
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of people attending the meeting.",
            },
            "date": {
                "type": "string",
                "description": "Date of the meeting (e.g., '2024-07-29')",
            },
            "time": {
                "type": "string",
                "description": "Time of the meeting (e.g., '15:00')",
            },
            "topic": {
                "type": "string",
                "description": "The subject or topic of the meeting.",
            },
        },
        "required": ["attendees", "date", "time", "topic"],
    },
}

# Configure the client and tools
client = genai.Client(api_key="AIzaSyDKLQONElGnqtXPO9Ccf5_-fvnpkAiNrf4")
tools = types.Tool(function_declarations=[schedule_meeting_function])
config = types.GenerateContentConfig(tools=[tools])

# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Schedule a meeting with Bob and Alice for 03/14/2025 at 10:00 AM about the Q3 planning.",
    config=config,
)


def schedule_meeting(attendees, date, time, topic):
    # Placeholder implementation of the scheduling function
    return f"Meeting scheduled with {', '.join(attendees)} on {date} at {time} about '{topic}'."


# Check for a function call
if response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(f"Function to call: {function_call.name}")
    print(f"Arguments: {function_call.args}")
    #  In a real app, you would call your function here:
    #  result = schedule_meeting(**function_call.args)
    if function_call.name == "schedule_meeting":
        args = function_call.args
        result = schedule_meeting(
            attendees=args["attendees"],
            date=args["date"],
            time=args["time"],
            topic=args["topic"],
        )
    client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"The meeting has been scheduled successfully: {result}",
    )

else:
    print("No function call found in the response.")
    print(response.text)
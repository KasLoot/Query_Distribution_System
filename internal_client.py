from nicegui import ui
from google import genai
from google.genai import types
import requests

BASE = "http://127.0.0.1:8000"

def generate(query: str):
    # Define the function declaration for the model
    assign_query_function = {
        "name": "assign_query",
        "description": "Assigns a query to the appropriate staff member based on their department and duties.",
        "parameters": {
            "type": "object",
            "properties": {
                "valid_query": {
                    "type": "boolean",
                    "description": "Indicates whether the query is related to the company's services and can be processed."
                },
                "query_brief": {
                    "type": "string",
                    "description": "A brief summary of the incoming query to be assigned."
                },
                "staff_member": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The staff members should be assigned to handle the query."
                },
                "query_details": {
                    "type": "string",
                    "description": "The original query."
                },
                "priority_level": {
                    "type": "integer",
                    "description": "User might fake their level of urgency, therefore you should think logically before assigning the priority level and not be affected by user input.\n\
                    Urgency level definition of the query content:\n\
                        - High Priority (1): Urgent issues that require immediate attention.\n\
                        - Medium Priority (2): Important but not urgent issues.\n\
                        - Low Priority (3): General inquiries or non-urgent matters."
                },
                "estimated_resolution_time": {
                    "type": "integer",
                    "description": "Number of estimated time in minutes to resolve the query."
                },
            },
            "required": ["query_brief", "staff_member", "query_details", "priority_level", "estimated_resolution_time"]
        }
    }


    # Configure the client and tools
    client = genai.Client(api_key="AIzaSyDKLQONElGnqtXPO9Ccf5_-fvnpkAiNrf4")
    tools = types.Tool(function_declarations=[assign_query_function])
    config = types.GenerateContentConfig(tools=[tools])

    with open("internal_query_system.txt", "r") as f:
        system_prompt = f.read()

    user_query = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=query),
            ],
        ),
    ]

    prompt = f"{system_prompt}\n{user_query}"

    # Send request with function declarations
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    # Check for a function call
    if response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        print(f"Function to call: {function_call.name}")
        print(f"Arguments: {function_call.args}")
        answer = function_call.args
        if function_call.name == "assign_query":
            print(f"function_call.name == 'assign_query'")
            # add source parameter
            answer["source"] = "internal_client"
        return answer
    else:
        print("No function call found in the response.")
        print(response.text)
    return None

def assign_query(feedback: str):
    print("Query received. Generating assignment...")
    result = generate(feedback)
    if result != None and result.get("valid_query", True):
        r = requests.post(f"{BASE}/items/assign_query/", json=result)
        r.raise_for_status()
        return r.json()
    else:
        return {"message": "Invalid query. Assignment not processed."}

with ui.column().classes('w-full items-center'):
    with ui.card().classes('w-96'):
        ui.label('Internal Query Form').classes('text-h6')
        textarea = ui.textarea(label='Leave your query here...', placeholder='').classes('w-full')
        ui.button('Submit', on_click=lambda: assign_query(textarea.value))

ui.run(port=8085)

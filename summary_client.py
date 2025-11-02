from nicegui import ui
from google import genai
from google.genai import types
import requests



BASE = "http://127.0.0.1:8000"

def generate(query: str):
    # Define the function declaration for the model
    generate_summary_function = {
        "name": "generate_summary_report",
        "description": "Generate a comprehensive weekly summary report analyzing the query data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query_weekly_report": {
                    "type": "string",
                    "description": "Analyze the weekly query and provide a summary report in 500 words."
                },
            },
            "required": ["query_weekly_report"]
        }
    }


    # Configure the client and tools
    client = genai.Client(api_key="AIzaSyDKLQONElGnqtXPO9Ccf5_-fvnpkAiNrf4")
    tools = types.Tool(function_declarations=[generate_summary_function])
    config = types.GenerateContentConfig(tools=[tools])

    with open("summary_report_system.txt", "r") as f:
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
        if function_call.name == "generate_summary_report":
            print(f"Successfully generated summary report")
            return function_call.args
    else:
        print("No function call found in the response.")
        print(response.text)
    return None

def fetch_weekly_queries():
    r = requests.get(f"{BASE}/items/fetch_weekly_queries/")
    fetched_data = r.json()
    r.raise_for_status()
    return fetched_data


def summarize_weekly_report(usr_generation_prompt):
    fetched_data = fetch_weekly_queries()
    result = generate(f"Query Data: {fetched_data}\nUser Generation Preference: {usr_generation_prompt}")
    return result


if __name__ in {"__main__", "__mp_main__"}:
    with ui.column().classes('w-full items-center'):
        with ui.card().classes('w-96'):
            ui.label('Weekly Query Summary').classes('text-h6')
            textarea = ui.textarea(label='How would you summarize the weekly queries?',
                                placeholder='').classes('w-full')
            def on_submit():
                print("Generating summary report...")
                summary = summarize_weekly_report(textarea.value)
                report_content = summary.get('query_weekly_report', 'No report generated.')
                output_markdown.set_content(f"**Weekly Summary Report:**\n\n{report_content}")
            ui.button('Generate Summary Report', on_click=on_submit).classes('mt-2')
        with ui.card().classes('w-96 mt-4'):
            output_markdown = ui.markdown('*Summary Report will appear here.*')

    ui.run(port=8081)
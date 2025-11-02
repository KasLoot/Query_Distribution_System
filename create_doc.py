from __future__ import print_function
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes: Docs for editing; Drive for listing/metadata (optional)
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file"  # lets app create files it owns
]

def get_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def main():
    creds = get_creds()

    # 1) Create the doc (Docs API can create & returns documentId)
    docs = build("docs", "v1", credentials=creds)
    doc = docs.documents().create(body={"title": "My Programmatic Doc"}).execute()
    document_id = doc.get("documentId")
    print("Created doc:", document_id)

    # 2) Write some content
    requests = [
        {"insertText": {
            "location": {"index": 1},  # 1 = just after start
            "text": "Hello from Python! 🎉\nThis was created via the Google Docs API.\n"
        }},
        # Example: make the first line a Heading 1
        {"updateParagraphStyle": {
            "range": {"startIndex": 1, "endIndex": 1 + len("Hello from Python! 🎉\n")},
            "paragraphStyle": {"namedStyleType": "HEADING_1"},
            "fields": "namedStyleType"
        }}
    ]
    docs.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

    # 3) (Optional) Get a shareable link (Drive API)
    drive = build("drive", "v3", credentials=creds)
    file = drive.files().get(fileId=document_id, fields="id, webViewLink, name").execute()
    print("Title:", file["name"])
    print("Open:", file["webViewLink"])

if __name__ == "__main__":
    main()

# google api

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_credentials():
    creds = None
    # token.json automatically created upon first connection. check if it exist
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # if cred are not valid
    if not creds or not creds.valid:
        print('not valid cred')
        if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
        else:
            print('cred')
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
    return creds


def connect_to_sheet(creds: Credentials, spreadsheet_id: str, range: str):
    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=spreadsheet_id, range=range)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return None

        return values

    except HttpError as err:
        print(err)
        return None

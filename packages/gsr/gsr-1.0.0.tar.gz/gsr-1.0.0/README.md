# Google Sheet Reader

Connect to your google sheet and export data.

To get your API token:
[Google Sheet Python quickstart](https://developers.google.com/workspace/sheets/api/quickstart/python)

## Install
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Example
```python
import gsr

if __name__ == '__main__':
    SHEET_ID = 'YOUR_SHEET_ID'
    creds = gsr.get_credentials()   # your creds should be name `credentials.json` and put in your working folder

    for range in ["Sheet1", "Sheet2", "Sheet3"]: # your sheet name
        print(f"GET {range}")

        values = gsr.connect_to_sheet(creds, SHEET_ID, range)

        if values is None:
            print(f"Error getting {range}, check your SHEET_ID or range")
        else:
            filename = 'csv_' + range + '.csv'
            with open(filename, 'w') as f:
                for row in values:
                    text = str(row) + '\n'
                    f.write(text)
```

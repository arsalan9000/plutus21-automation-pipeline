# main.py
import os
import json
import sqlite3
import google.generativeai as genai
import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
load_dotenv() # Loads variables from .env file

# Load secrets and config from environment variables
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service_account.json'
DB_FILE = 'opportunities.db'
SHEET_NAME = 'Form Responses 1' # Usually 'Sheet1' unless you renamed it

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')

# --- FUNCTIONS ---

def get_google_sheets_service():
    """Authenticates and returns a Google Sheets service object."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=GOOGLE_SHEETS_SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

def fetch_new_inquiries(service):
    """Fetches all rows from the sheet and filters for new ones."""
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f'{SHEET_NAME}!A:H').execute()
    values = result.get('values', [])
    
    if not values or len(values) < 2:
        print("No data found or only header row.")
        return []

    # Assumes header row is present
    header = values[0]
    all_rows = values[1:]
    
    new_inquiries = []
    for i, row in enumerate(all_rows):
        row_dict = dict(zip(header, row))
        # Check if the 'Status' column is empty or missing
        if row_dict.get('Status', '').strip() == '':
            row_dict['row_index'] = i + 2 # +2 because sheet is 1-indexed and we skipped header
            new_inquiries.append(row_dict)
            
    print(f"Found {len(new_inquiries)} new inquiries.")
    return new_inquiries

def analyze_with_ai(description):
    """Uses Gemini AI to analyze the opportunity description."""
    prompt = f"""
    As a venture capital analyst, review the following inbound partnership opportunity.
    Our investment thesis focuses on B2B SaaS companies in Pakistan with early traction.

    Opportunity Description: "{description}"

    Analyze the description and provide a JSON object with three keys:
    1. "summary": A one-sentence summary of the company's business model.
    2. "alignment_score": An integer score from 1 (poor fit) to 5 (perfect fit) based on our investment thesis.
    3. "suggested_next_step": A brief, actionable next step for our team (e.g., "Request pitch deck," "Schedule initial screening call," or "Forward to portfolio company for partnership").

    Respond with ONLY the valid JSON object and nothing else.
    """
    try:
        response = model.generate_content(prompt)
        # Clean up the response to ensure it's valid JSON
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        ai_result = json.loads(cleaned_response)
        print(f"AI Analysis successful: Score = {ai_result.get('alignment_score')}")
        return ai_result
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return None

def store_in_database(inquiry, ai_result):
    """Stores the inquiry and its analysis in the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO opportunities (timestamp, company_name, contact_email, company_website, description, status, ai_summary, alignment_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inquiry.get('Timestamp'),
        inquiry.get('Company Name'),
        inquiry.get('Contact Email'),
        inquiry.get('Company Website'),
        inquiry.get('Opportunity Description'),
        'Processed',
        ai_result.get('summary'),
        ai_result.get('alignment_score')
    ))
    conn.commit()
    conn.close()
    print(f"Stored '{inquiry.get('Company Name')}' in the database.")

def send_slack_alert(inquiry, ai_result):
    """Sends a formatted alert to a Slack channel."""
    if ai_result.get('alignment_score', 0) < 4:
        print("Skipping Slack alert for low-priority item.")
        return

    message = {
        "text": f"🚀 High-Priority Opportunity: *{inquiry.get('Company Name')}* (Score: {ai_result.get('alignment_score')}/5)",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚀 *High-Priority Opportunity: {inquiry.get('Company Name')}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Alignment Score:*\n{ai_result.get('alignment_score')}/5"},
                    {"type": "mrkdwn", "text": f"*Contact:*\n{inquiry.get('Contact Email')}"}
                ]
            },
            {
			    "type": "section",
			    "text": {
					"type": "mrkdwn",
					"text": f"*Summary:*\n{ai_result.get('summary')}"
				}
		    },
            {
			    "type": "section",
			    "text": {
					"type": "mrkdwn",
					"text": f"*Suggested Next Step:*\n>{ai_result.get('suggested_next_step')}"
				}
		    }
        ]
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=message)
    if response.status_code == 200:
        print("Slack alert sent successfully.")
    else:
        print(f"Failed to send Slack alert. Status: {response.status_code}, Response: {response.text}")


def update_sheet(service, row_index, ai_result):
    """Updates the Google Sheet with the status and AI results."""
    values = [
        ['Processed', ai_result.get('summary'), ai_result.get('alignment_score')]
    ]
    body = {'values': values}
    # Update starting from column F (Status) for the specific row
    range_to_update = f'{SHEET_NAME}!F{row_index}' 
    
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_to_update,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print(f"Updated Google Sheet at row {row_index}.")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("--- Starting Automation Pipeline ---")
    sheets_service = get_google_sheets_service()
    new_inquiries = fetch_new_inquiries(sheets_service)

    if not new_inquiries:
        print("No new inquiries to process. Exiting.")
    else:
        for inquiry in new_inquiries:
            print(f"\nProcessing inquiry from: {inquiry.get('Company Name')}")
            
            description = inquiry.get('Opportunity Description')
            if not description:
                print("Skipping inquiry with no description.")
                continue

            # Step 1: Analyze with AI
            ai_analysis = analyze_with_ai(description)
            if not ai_analysis:
                print("Skipping due to AI analysis failure.")
                continue

            # Step 2: Store in Database
            store_in_database(inquiry, ai_analysis)

            # Step 3: Send Slack Alert (if high priority)
            send_slack_alert(inquiry, ai_analysis)

            # Step 4: Update the Google Sheet to close the loop
            update_sheet(sheets_service, inquiry['row_index'], ai_analysis)
            
    print("\n--- Automation Pipeline Finished ---")
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class DataHandler:
    def __init__(self):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        self.sheet_url = st.secrets.get("google_sheet_url")
        self.client = None
        self.sheet = None
        
        # Try to connect to Google Sheets
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                self.creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.scope)
                self.client = gspread.authorize(self.creds)
                if self.sheet_url:
                    self.sheet = self.client.open_by_url(self.sheet_url).sheet1
            else:
                print("Google Cloud Service Account secrets not found. Using local CSV fallback.")
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")

    def log_data(self, session_data):
        """
        Logs data to Google Sheet if available, else appends to local CSV.
        session_data: dict containing timestamp, condition, chat_log, survey_responses
        """
        
        # Format for saving
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Flatten simple dictionary for Sheet row
        row_data = [
            session_data.get("session_id"),
            timestamp,
            session_data.get("condition"),
            json.dumps(session_data.get("chat_history")), # Store full chat as JSON string
            session_data.get("survey_knowledge"),
            session_data.get("survey_empathy"),
            session_data.get("survey_comments")
        ]
        
        # 1. Try Google Sheets
        if self.sheet:
            try:
                self.sheet.append_row(row_data)
                print("Logged to Google Sheet")
                return True
            except Exception as e:
                print(f"Failed to write to Google Sheet: {e}")
        
        # 2. Fallback to Local CSV
        try:
            df = pd.DataFrame([row_data], columns=[
                "Session ID", "Timestamp", "Condition", "Chat History", "Knowledge Rating", "Empathy Rating", "Comments"
            ])
            # Append to file, if file does not exist write header
            with open("experiment_logs.csv", "a") as f:
                df.to_csv(f, header=f.tell()==0, index=False)
            print("Logged to local CSV")
            return True
        except Exception as e:
            print(f"Failed to log locally: {e}")
            return False

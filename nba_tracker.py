import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import smtplib
from email.mime.text import MIMEText

# Set up Google Sheets credentials
creds_file = "credentials.json"
with open(creds_file, "w") as f:
    f.write(os.environ["GOOGLE_SHEETS_CREDS"])

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
client = gspread.authorize(creds)
sheet = client.open("NBA Player Tracker").sheet1

# NBA API endpoint (placeholder – update if you have a real source)
NBA_STATS_API = "https://api.example.com/nba/game_stats"

def fetch_recent_game_stats():
    today = datetime.today().date()
    params = {"date": today.isoformat()}
    response = requests.get(NBA_STATS_API, params=params)
    return response.json() if response.status_code == 200 else []

def filter_players(stats):
    filtered = []
    for player in stats:
        first_5_min = player.get("first_5_min", {})
        if (first_5_min.get("points", 0) >= 6 or
            first_5_min.get("rebounds", 0) >= 3 or
            first_5_min.get("assists", 0) >= 3):
            filtered.append(player)
    return filtered

def update_google_sheet(players):
    rows = []
    for p in players:
        rows.append([
            p.get("name"),
            p.get("team"),
            p.get("opponent"),
            p.get("first_5_min", {}).get("points", 0),
            p.get("first_5_min", {}).get("rebounds", 0),
            p.get("first_5_min", {}).get("assists", 0),
            p.get("full_game", {}).get("points", 0),
            p.get("full_game", {}).get("rebounds", 0),
            p.get("full_game", {}).get("assists", 0),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    if rows:
        sheet.append_rows(rows, value_input_option="RAW")

def send_email_alert(players):
    if not players:
        return

    GMAIL_SENDER = os.environ.get("GMAIL_SENDER")
    GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
    GMAIL_RECEIVER = os.environ.get("GMAIL_RECEIVER")

    subject = "NBA Bet Tracker Alert"
    message = "\n\n".join([
        f"{p['name']} vs {p['opponent']} - First 5 Min: {p['first_5_min']} | Full Game: {p['full_game']}"
        for p in players
    ])
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECEIVER

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_SENDER, GMAIL_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    stats = fetch_recent_game_stats()
    filtered_players = filter_players(stats)
    update_google_sheet(filtered_players)
    send_email_alert(filtered_players)

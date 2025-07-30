import Portfolio
import Order
import Execution
import os
import csv
import gspread
from datetime import datetime

class tradeSim:

    def __init__(self, team_name, load_existing=False, file_path="portfolio.json"):
        if load_existing and os.path.exists(file_path):
            self.portfolio = Portfolio.portfolio.load_from_file(file_path)
            print(f"[INFO] Loaded existing portfolio from '{file_path}'")
        else:
            self.portfolio = Portfolio.portfolio(team_name)
            print(f"[INFO] Created new portfolio for '{team_name}'")

        self.execution = Execution.execution()

    def create_order(self, volume, price, side, symbol, time, mkt_data):
        new_order = Order.order(
            ownerPortfolio=self.portfolio,
            volume=volume,
            price=price,
            side=side,
            symbol=symbol,
            timestamp=time
        )
        self.execution.addOrderToOrders_Book(new_order, mkt_data)

    def get_execution(self):
        return self.execution

    def get_portfolio(self):
        return self.portfolio

    def export_portfolio_to_csv(self,credentials, filename="portfolio_summary.csv"):
        if not self.portfolio:
            print("[ERROR] No portfolio to export.")
            return

        summary = self.portfolio.get_portfolio_info()
        if not isinstance(summary, dict):
            print("[ERROR] get_portfolio_info() did not return a dictionary.")
            return

        # --- Save CSV ---
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=summary.keys())
            writer.writeheader()
            writer.writerow(summary)
        print(f"[INFO] Portfolio summary exported to '{filename}'")

        # --- Google Sheets Upload Config ---
        CSV_FILE = filename
        SHEET_TITLE = 'Portfolios Trading Simulation'
        SHEET_NAME = datetime.now().strftime("%Y-%m-%d")  # New worksheet per day
        YOUR_EMAIL = 'poramet.kaew@gmail.com'
        gc = gspread.authorize(credentials)

        # --- Load CSV Data ---
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = list(reader)

        if len(data) < 2 or len(data[1]) == 0:
            raise ValueError("[ERROR] CSV file must contain at least one data row with owner name.")
        
        headers = data[0]
        owner_name = data[1][0]

        # --- Spreadsheet Check ---
        try:
            spreadsheet = gc.open(SHEET_TITLE)
            print(f"[INFO] Found spreadsheet: '{SHEET_TITLE}'")
        except gspread.SpreadsheetNotFound:
            spreadsheet = gc.create(SHEET_TITLE)
            spreadsheet.share(YOUR_EMAIL, perm_type='user', role='writer')
            print(f"[INFO] Created spreadsheet: '{SHEET_TITLE}'")

        # --- Worksheet Check (per day) ---
        try:
            worksheet = spreadsheet.worksheet(SHEET_NAME)
            print(f"[INFO] Found worksheet for today: '{SHEET_NAME}'")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows="1000", cols="20")
            print(f"[INFO] Created new worksheet for today: '{SHEET_NAME}'")
            worksheet.append_row(headers)  # Add headers when new

        # --- Read current data in worksheet ---
        sheet_data = worksheet.get_all_values()

        # Check if owner already exists
        owner_row_index = None
        for i, row in enumerate(sheet_data[1:], start=2):  # Skip header, 1-based index
            if row and row[0].strip().lower() == owner_name.strip().lower():
                owner_row_index = i
                break

        if owner_row_index:
            worksheet.update(f"A{owner_row_index}", [data[1]])
            print(f"[INFO] Overwrote existing data for owner '{owner_name}' at row {owner_row_index}")
        else:
            worksheet.append_row(data[1])
            print(f"[INFO] Appended new data for owner '{owner_name}'")



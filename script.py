import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
import subprocess

# Constants
BASE_URL = "https://omitnomis.github.io/ShareSansarScraper/Data"
BASE_DIR = Path(__file__).resolve().parent
SCRAPE_DIR = BASE_DIR / "Scrape-StockPrice"
OUTPUT_DIR = BASE_DIR / "Output"

def show_help():
    print("""
🛠️ Nepse SCRAPER & ANALYZER – Help Menu

Usage:
  python script.py [--daily | --weekly | --monthly] [--date=YYYY-MM-DD]

Options:
  --daily            Scrape and consolidate data for the past 30 days (3-day intervals).
  --weekly           Scrape and consolidate data for the past 10 weeks.
  --monthly          Scrape and consolidate data from 1, 3, 6, and 9 months ago.
  --date=YYYY-MM-DD  Optional: Specify a custom reference date for scraping.
  --help             Show this help menu.

Examples:
  python script.py --daily
  python script.py --weekly --date=2024-12-01
""")
    sys.exit(0)

def cleanup(downloaded_files):
    print("\n🧹 Cleaning up scraped CSV files...")
    for file in downloaded_files:
        try:
            os.remove(file)
            print(f"🗑️ Deleted: {file}")
        except Exception as e:
            print(f"⚠️ Failed to delete {file}: {e}")

def open_csv(file_path):
    print(f"\n📂 Opening CSV: {file_path}")
    try:
        if sys.platform.startswith("win"):
            os.startfile(file_path)
        elif sys.platform.startswith("darwin"):
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])
    except Exception as e:
        print(f"⚠️ Could not open file automatically: {e}")

def download_csv(date_obj: datetime, subfolder: str):
    filename = date_obj.strftime("%Y_%m_%d.csv")
    url = f"{BASE_URL}/{filename}"
    save_path = SCRAPE_DIR / subfolder / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded: {filename}")
        return save_path
    else:
        print(f"❌ Failed to download: {filename}")
        return None

def build_dates(mode: str, ref_date: datetime):
    dates = [ref_date]
    if mode == '--daily':
        for i in range(1, 10):
            dates.append(ref_date - timedelta(days=i * 3))
    elif mode == '--weekly':
        for i in range(1, 10):
            dates.append(ref_date - timedelta(days=i * 7))
    elif mode == '--monthly':
        for i in [1, 3, 6, 9]:
            dates.append(ref_date - relativedelta(months=i))
    else:
        raise ValueError("Invalid mode. Use --daily, --weekly or --monthly")
    return [d.replace(hour=0, minute=0, second=0, microsecond=0) for d in dates]

def load_dataframes(date_list, subfolder, downloaded_files):
    frames = {}
    for d in date_list:
        path = download_csv(d, subfolder)
        if path and path.exists():
            try:
                df = pd.read_csv(path)
                df = df[['Symbol', 'Close']].copy()
                df['Close'] = df['Close'].astype(str).str.replace(',', '').astype(float)
                frames[d.strftime("%d.%m.%Y")] = df
                downloaded_files.append(str(path))
            except Exception as e:
                print(f"⚠️ Error reading/parsing {path.name}: {e}")
    return frames

def consolidate_data(frames: dict):
    result_df = None
    for date, df in frames.items():
        df = df.rename(columns={'Close': f'{date}_Close'})
        if result_df is None:
            result_df = df
        else:
            result_df = pd.merge(result_df, df, on='Symbol', how='outer')
    return result_df

def calculate_percentage(df, date_columns):
    try:
        first_col = f"{date_columns[-1]}_Close"
        last_col = f"{date_columns[0]}_Close"

        diffs = []
        for col in date_columns[1:]:
            comp_col = f"{col}_Close"
            diff = (df[last_col] - df[comp_col]) / df[comp_col]
            diffs.append(diff)
        df['+/- Momentum %'] = (sum(diffs) * 100).round(2).astype(str) + "%"

        df['Overall %'] = (((df[last_col] - df[first_col]) / df[first_col]) * 100).round(2).astype(str) + "%"

        def label(row):
            try:
                perc = float(row['+/- Momentum %'].replace('%', ''))
                return 'Up' if perc > 0 else 'Down' if perc < 0 else 'No Change'
            except:
                return 'No Change'

        df['Trend'] = df.apply(label, axis=1)

    except Exception as e:
        print("Error calculating percentages:", e)
    return df

def parse_args():
    print("Select scraping mode:")
    print("[1] Daily")
    print("[2] Weekly")
    print("[3] Monthly")
    print("[4] Exit")
    choice = input("Enter choice (1/2/3/4): ").strip()

    if choice == "4":
        sys.exit(0)
    elif choice == "1":
        mode = "--daily"
    elif choice == "2":
        mode = "--weekly"
    elif choice == "3":
        mode = "--monthly"
    else:
        print("Invalid choice.")
        sys.exit(1)

    today_choice = input("Do you want to use today's date? (Y/N): ").strip().lower()
    if today_choice == "y":
        custom_date = None
    else:
        while True:
            date_input = input("Enter custom date (YYYY-MM-DD): ").strip()
            try:
                custom_date = datetime.strptime(date_input, "%Y-%m-%d")
                break
            except ValueError:
                print("Invalid date format. Try again.")
    return mode, custom_date


# Main
if __name__ == '__main__':
    downloaded_files = []
    output_file = None

    try:
        mode, custom_date = parse_args()
        ref_date = custom_date or datetime.today()

        subfolder_map = {
            '--daily': '3-days',
            '--weekly': 'weekly',
            '--monthly': 'monthly'
        }
        output_folder_map = {
            '--daily': OUTPUT_DIR / '3-Day-Consolidated',
            '--weekly': OUTPUT_DIR / 'Weekly-Consolidated',
            '--monthly': OUTPUT_DIR / 'Montly-Consolidated'
        }

        dates = build_dates(mode, ref_date)
        subfolder = subfolder_map[mode]
        output_folder = output_folder_map[mode]
        output_folder.mkdir(parents=True, exist_ok=True)

        print(f"📊 Scraping for {mode[2:]} mode...")
        frames = load_dataframes(dates, subfolder, downloaded_files)
        if not frames:
            print("⚠️ No data to process.")
            sys.exit(1)

        consolidated_df = consolidate_data(frames)
        date_keys = list(frames.keys())
        consolidated_df = calculate_percentage(consolidated_df, date_keys)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = output_folder / f"consolidated-{mode[2:]}-{timestamp}.csv"
        consolidated_df.to_csv(output_file, index=False)
        print(f"\n✅ CSV saved to {output_file}")

        cleanup(downloaded_files)
        open_csv(output_file)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        cleanup(downloaded_files)
        sys.exit(1)

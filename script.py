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

# Helper: Clean up downloaded CSV files
def cleanup(downloaded_files):
    print("\n🧹 Cleaning up scraped CSV files...")
    for file in downloaded_files:
        try:
            os.remove(file)
            print(f"🗑️ Deleted: {file}")
        except Exception as e:
            print(f"⚠️ Failed to delete {file}: {e}")

# Helper: Open CSV with default application
def open_csv(file_path):
    print(f"\n📂 Opening CSV: {file_path}")
    try:
        if sys.platform.startswith("win"):
            os.startfile(file_path)
        elif sys.platform.startswith("darwin"):
            subprocess.run(["open", file_path])
        else:  # Assume Linux
            subprocess.run(["xdg-open", file_path])
    except Exception as e:
        print(f"⚠️ Could not open file automatically: {e}")

# Download CSV file from URL
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

# Build date list based on mode
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

# Load and parse CSVs into a dictionary {date: DataFrame}
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

# Merge all dataframes into one comparison table
def consolidate_data(frames: dict):
    result_df = None
    for date, df in frames.items():
        df = df.rename(columns={'Close': f'{date}_Close'})
        if result_df is None:
            result_df = df
        else:
            result_df = pd.merge(result_df, df, on='Symbol', how='outer')
    return result_df

# Calculate +/- Momentum % and Overall %
def calculate_percentage(df, date_columns):
    try:
        first_col = f"{date_columns[-1]}_Close"
        last_col = f"{date_columns[0]}_Close"

        # +/- Momentum %
        diffs = []
        for col in date_columns[1:]:
            comp_col = f"{col}_Close"
            diff = (df[last_col] - df[comp_col]) / df[comp_col]
            diffs.append(diff)
        df['+/- Momentum %'] = (sum(diffs) * 100).round(2).astype(str) + "%"

        # Simple overall percentage
        df['Overall %'] = (((df[last_col] - df[first_col]) / df[first_col]) * 100).round(2).astype(str) + "%"

        # Label
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

# Parse command-line arguments
def parse_args():
    mode = None
    custom_date = None
    for arg in sys.argv[1:]:
        if arg.startswith("--date="):
            date_str = arg.split("=", 1)[1]
            try:
                custom_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print("❌ ERROR: Invalid date format. Use --date=YYYY-MM-DD")
                sys.exit(1)
        elif arg in ["--daily", "--weekly", "--monthly"]:
            mode = arg

    if not mode:
        print("Usage: python script.py --daily | --weekly | --monthly [--date=YYYY-MM-DD]")
        sys.exit(1)

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
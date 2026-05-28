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
  --daily            Scrape past 30 days (3-day intervals)
  --weekly           Scrape past 10 weeks
  --monthly          Scrape 1, 3, 6, 9 months back
  --date=YYYY-MM-DD  Custom reference date
  --help             Help menu
""")
    sys.exit(0)

def cleanup(downloaded_files):
    print("\n🧹 Cleaning up scraped CSV files...")
    for file in downloaded_files:
        try:
            os.remove(file)
        except:
            pass

def open_csv(file_path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(file_path)
        elif sys.platform.startswith("darwin"):
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])
    except:
        pass

def download_csv(date_obj: datetime, subfolder: str):
    filename = date_obj.strftime("%Y_%m_%d.csv")
    url = f"{BASE_URL}/{filename}"
    save_path = SCRAPE_DIR / subfolder / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    r = requests.get(url)
    if r.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path
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

    return [d.replace(hour=0, minute=0, second=0, microsecond=0) for d in dates]

def load_dataframes(date_list, subfolder, downloaded_files):
    frames = {}
    missing_dates = []

    for d in date_list:
        path = download_csv(d, subfolder)
        if path and path.exists():
            df = pd.read_csv(path)
            df = df[['Symbol', 'Close']].copy()
            df['Close'] = df['Close'].astype(str).str.replace(',', '').astype(float)
            frames[d.strftime("%d.%m.%Y")] = df
            downloaded_files.append(str(path))
        else:
            missing_dates.append(d.strftime("%Y-%m-%d"))

    if missing_dates:
        print(f"\n⚠️  No data found for {len(missing_dates)} date(s) (weekend/holiday/not yet published):")
        for md in missing_dates:
            print(f"   • {md}")

    if not frames:
        print("\n❌ No data could be fetched for any of the requested dates.")
    else:
        print(f"\n✅ Data loaded for {len(frames)} of {len(date_list)} requested dates.")

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
    first_col = f"{date_columns[-1]}_Close"
    last_col = f"{date_columns[0]}_Close"

    diffs = []
    for col in date_columns[1:]:
        comp_col = f"{col}_Close"
        diffs.append((df[last_col] - df[comp_col]) / df[comp_col])

    df['+/- Momentum %'] = (sum(diffs) * 100).round(2).astype(str) + "%"

    df['Overall %'] = (((df[last_col] - df[first_col]) / df[first_col]) * 100).round(2).astype(str) + "%"

    def label(row):
        try:
            val = float(row['+/- Momentum %'].replace('%', ''))
            return 'Up' if val > 0 else 'Down' if val < 0 else 'No Change'
        except:
            return 'No Change'

    df['Trend'] = df.apply(label, axis=1)

    return df

def reorder_columns(df):
    date_cols = [c for c in df.columns if c.endswith("_Close")]

    ordered = (
        ['Symbol', '+/- Momentum %', 'Overall %', 'Trend']
        + date_cols
    )

    return df[ordered]

def parse_args():
    mode = None
    custom_date = None

    for arg in sys.argv[1:]:
        if arg == "--help":
            show_help()

        elif arg.startswith("--date="):
            custom_date = datetime.strptime(arg.split("=")[1], "%Y-%m-%d")

        elif arg in ["--daily", "--weekly", "--monthly"]:
            mode = arg

        elif arg.startswith("--scrape-dir="):
            global SCRAPE_DIR
            SCRAPE_DIR = Path(arg.split("=")[1])

        elif arg.startswith("--output-dir="):
            global OUTPUT_DIR
            OUTPUT_DIR = Path(arg.split("=")[1])

    if not mode:
        print("Missing mode")
        sys.exit(1)

    return mode, custom_date


if __name__ == "__main__":
    downloaded_files = []

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
            '--monthly': OUTPUT_DIR / 'Monthly-Consolidated'
        }

        dates = build_dates(mode, ref_date)

        frames = load_dataframes(dates, subfolder_map[mode], downloaded_files)

        if not frames:
            sys.exit(1)

        df = consolidate_data(frames)
        date_keys = list(frames.keys())

        df = calculate_percentage(df, date_keys)

        df = reorder_columns(df)

        output_folder = output_folder_map[mode]
        output_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = output_folder / f"consolidated-{mode[2:]}-{timestamp}.csv"

        df.to_csv(output_file, index=False)

        cleanup(downloaded_files)
        open_csv(output_file)

        print(f"\n📁 Saved: {output_file}")

    except Exception as e:
        print(f"ERROR: {e}")
        cleanup(downloaded_files)
        sys.exit(1)

🙏 Thanks to [OmitNomis](https://github.com/OmitNomis/ShareSansarScraper) for the original ShareSansar data scraping sources!




# Nepse-SCRAPER & ANALYZER 📊

This tool scrapes, consolidates, and analyzes NEPSE (Nepal Stock Exchange) stock prices across multiple time intervals

 3-day difference, 
 weekly, 
 and monthly — and outputs clean, structured CSV/Excel files ready for comparison.



## 📁 Project Structure



        ├───Output
        │   ├───3-Day-Consolidated
        │   ├───Montly-Consolidated
        │   └───Weekly-Consolidated
        ├───Recent-Comparison
        └───Scrape-StockPrice
        ├    ├───3-days
        ├    ├───monthly
        ├    └───weekly   
        ├─── script.py
        ├─── requirement.txt



## Usage

### macOS launcher

Download `Nepse.dmg` from the repository and open it to access the macOS launcher. The launcher is also available as `NEPSE.command`; double-click it in Finder to start the interactive menu. Choose daily, weekly, or monthly analysis, then choose today, yesterday, or a custom date. The launcher installs its Python dependencies in a temporary virtual environment, downloads the latest `script.py`, and saves generated files under `/tmp/Scrape-StockPrice` and `/tmp/Scraped-Excels`.

The launcher requires macOS, Python 3, and an internet connection. The first run may take longer while dependencies are installed.

### Python script

## 🔧 Setup

1. Clone the repository:
   
   `git clone https://github.com/sujoff/stocks-analyzer-pyscript.git`

   `cd stocks-analyzer-pyscript`


Install dependencies:

    pip install -r requirement.txt


Run the script with one of the following options:


# For 3-day intervals (scrapes 10 latest files)
`python script.py --daily`

# For weekly intervals (scrapes 10 weeks)
`python script.py --weekly`

# For monthly intervals (scrapes 1, 3, 6, and 9 months ago)
`python script.py --monthly`

# For scraping data based on specific data, do:

        python script.py --date=2024-04-25 --weekly

        python script.py --date=2024-04-25 --daily

        python script.py --date=2024-04-25 --monthly


Each mode will:
- Download and store raw data under `Scrape-StockPrice/` folder
- Merge them into a consolidated CSV saved in `3-Day-Consolidated/`, `Weekly-Consolidated/`, or `Montly-Consolidated/`
- Generate an Excel comparison in `relevant consolidated directory` with stock names and their closing prices across selected dates

✅ **Latest data (including today's)** is automatically included in the consolidation.

---

## 📌 Notes

- Make sure you have a stable internet connection while scraping.
- All files are date-stamped and non-destructive (existing files won't be overwritten).
- Data source: https://omitnomis.github.io/ShareSansarScraper


---

## 🛠 Author

Made with ❤️💦 by sujan .

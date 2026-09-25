#!/bin/bash

# ─── Directories ────────────────────────────────────────────────
TEMP_SCRAPE="/tmp/Scrape-StockPrice"
OUTPUT_DIR="/tmp/Scraped-Excels"

PY_SCRIPT_URL="https://raw.githubusercontent.com/sujoff/stocks-analyzer-pyscript/refs/heads/main/script.py"
DOWNLOADED_SCRIPT="/tmp/script.py"

# Suppress harmless LibreSSL / urllib3 warning
export PYTHONWARNINGS="ignore::Warning:urllib3"

while true; do

clear

echo "=============================================================="
echo "        TRICKY NEPSE - STOCK MARKET ANALYZER"
echo "=============================================================="
echo

# ─── Mode Selection ─────────────────────────────────────────────
echo "[1] Daily"
echo "[2] Weekly"
echo "[3] Monthly"
echo "[4] Exit"
echo

read -p "Enter choice (1/2/3/4): " mode_choice

case $mode_choice in
    1) mode="--daily" ;;
    2) mode="--weekly" ;;
    3) mode="--monthly" ;;
    4) exit 0 ;;
    *) echo "Invalid choice"; sleep 1; continue ;;
esac

# ─── Date Selection ─────────────────────────────────────────────
echo
echo "[1] Today"
echo "[2] Yesterday"
echo "[3] Custom Date"
echo

read -p "Enter choice (1/2/3): " date_choice

custom_date=""

if [ "$date_choice" = "2" ]; then
    custom_date=$(date -v-1d +"%Y-%m-%d")

elif [ "$date_choice" = "3" ]; then
    echo
    echo "Opening date picker..."

    # Native macOS date picker via AppleScript
    picked=$(osascript <<'APPLESCRIPT'
        set today to current date
        set chosenDate to current date

        tell application "System Events"
            activate
        end tell

        set dialogResult to display dialog "Select a date for analysis:" & return & return & ¬
            "Enter date as YYYY-MM-DD" & return & ¬
            "(or click 'Pick' to use the calendar)" ¬
            buttons {"Cancel", "Manual Entry", "Pick Date"} ¬
            default button "Pick Date" ¬
            with title "NEPSE - Date Picker"

        set btnPressed to button returned of dialogResult

        if btnPressed is "Pick Date" then
            -- Calendar-style picker using choose from list for year/month/day
            set yearList to {}
            set currentYear to year of (current date)
            repeat with y from (currentYear - 2) to currentYear
                set end of yearList to y as string
            end repeat

            set chosenYear to item 1 of (choose from list yearList with prompt "Select Year:" with title "NEPSE Date Picker" default items {currentYear as string})
            if chosenYear is false then error "Cancelled"

            set monthNames to {"01 - January", "02 - February", "03 - March", "04 - April", "05 - May", "06 - June", "07 - July", "08 - August", "09 - September", "10 - October", "11 - November", "12 - December"}
            set chosenMonth to item 1 of (choose from list monthNames with prompt "Select Month:" with title "NEPSE Date Picker")
            if chosenMonth is false then error "Cancelled"
            set chosenMonthNum to text 1 thru 2 of chosenMonth

            set dayList to {}
            repeat with d from 1 to 31
                if d < 10 then
                    set end of dayList to "0" & (d as string)
                else
                    set end of dayList to d as string
                end if
            end repeat

            set chosenDay to item 1 of (choose from list dayList with prompt "Select Day:" with title "NEPSE Date Picker")
            if chosenDay is false then error "Cancelled"

            return chosenYear & "-" & chosenMonthNum & "-" & chosenDay

        else
            -- Manual text entry fallback
            set manualResult to display dialog "Enter date (YYYY-MM-DD):" ¬
                default answer (do shell script "date +%Y-%m-%d") ¬
                buttons {"Cancel", "OK"} default button "OK" ¬
                with title "NEPSE - Manual Date Entry"
            if button returned of manualResult is "Cancel" then error "Cancelled"
            return text returned of manualResult
        end if
APPLESCRIPT
    )

    # Check if user cancelled
    if [ $? -ne 0 ] || [ -z "$picked" ]; then
        echo "Date selection cancelled."
        sleep 1
        continue
    fi

    # Validate format YYYY-MM-DD
    if ! echo "$picked" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
        echo "Invalid date format: $picked"
        sleep 1
        continue
    fi

    custom_date="$picked"
    echo "Selected date: $custom_date"
fi

# ─── Setup ──────────────────────────────────────────────────────
VENV_DIR="/tmp/nepse_venv"

mkdir -p "$TEMP_SCRAPE"
mkdir -p "$OUTPUT_DIR"

if ! command -v python3 &> /dev/null; then
    echo "Python3 not found."
    sleep 2
    continue
fi

echo
echo "[1/3] Installing required packages..."
# Create a venv if it doesn't exist yet, then install into it
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --quiet pandas requests python-dateutil openpyxl

echo
echo "[2/3] Downloading latest engine..."
curl -sL "$PY_SCRIPT_URL" -o "$DOWNLOADED_SCRIPT"

if [ ! -s "$DOWNLOADED_SCRIPT" ]; then
    echo "Failed to download script."
    sleep 2
    continue
fi

# The upstream analyzer skips dates whose CSV is absent. Resolve each requested
# date first, preferring the closest available prior day (-1, then -2), and use
# the next day (+1) only when neither prior date has data.
"$VENV_DIR/bin/python3" - "$DOWNLOADED_SCRIPT" <<'PY'
from pathlib import Path
import sys

script = Path(sys.argv[1])
source = script.read_text()
marker = 'if __name__ == "__main__":'
if marker not in source:
    raise SystemExit("Downloaded analyzer has an unexpected layout; cannot add date fallback.")

fallback = r'''
_original_build_dates = build_dates

def build_dates(mode: str, ref_date: datetime):
    resolved = []
    used = set()
    for requested in _original_build_dates(mode, ref_date):
        chosen = None
        for offset in (0, -1, -2, 1):
            candidate = requested + timedelta(days=offset)
            if candidate in used:
                continue
            filename = candidate.strftime("%Y_%m_%d.csv")
            url = f"{BASE_URL}/{filename}"
            try:
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    chosen = candidate
                    break
            except requests.RequestException:
                pass
        if chosen is not None:
            if chosen != requested:
                print(f"Using available data for {chosen:%Y-%m-%d} instead of {requested:%Y-%m-%d}.")
            resolved.append(chosen)
            used.add(chosen)
        else:
            print(f"No data found for {requested:%Y-%m-%d} or nearby fallback dates (-1, -2, +1).")
    return resolved

'''
script.write_text(source.replace(marker, fallback + marker, 1))
PY
if [ $? -ne 0 ]; then
    echo "Could not prepare date fallback in the downloaded analyzer."
    sleep 2
    continue
fi

echo
echo "[3/3] Running analysis..."

if [ -n "$custom_date" ]; then
    "$VENV_DIR/bin/python3" "$DOWNLOADED_SCRIPT" $mode --date="$custom_date" \
        --scrape-dir="$TEMP_SCRAPE" \
        --output-dir="$OUTPUT_DIR"
else
    "$VENV_DIR/bin/python3" "$DOWNLOADED_SCRIPT" $mode \
        --scrape-dir="$TEMP_SCRAPE" \
        --output-dir="$OUTPUT_DIR"
fi

echo
echo "=============================================================="
echo "✅ Completed. Output saved to:"
echo "   $OUTPUT_DIR"
echo "=============================================================="
echo
read -p "Press Enter to go back to main menu..."

done

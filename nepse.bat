@echo off
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
chcp 65001 >nul

:: Define ANSI colors
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "CYAN=[36m"
set "NC=[0m"

:: Define directories
set "TEMP_SCRAPE=%TEMP%\Scrape-StockPrice"
#set "OUTPUT_DIR=%~dp0Scraped Excels"
set "PY_SCRIPT_URL=https://raw.githubusercontent.com/sujoff/stocks-analyzer-pyscript/refs/heads/main/script.py"
set "DOWNLOADED_SCRIPT=%TEMP%\script.py"

:: Ensure OUTPUT_DIR exists
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

:: Main menu
:main
cls
call :banner

echo %YELLOW%Select scraping mode:%NC%
echo [1] Daily
echo [2] Weekly
echo [3] Monthly
echo [4] Exit

set "mode="
set /p mode_choice=Enter choice (1/2/3/4): 

if "%mode_choice%"=="4" goto end
if "%mode_choice%"=="1" set mode=--daily
if "%mode_choice%"=="2" set mode=--weekly
if "%mode_choice%"=="3" set mode=--monthly

if not defined mode (
    echo %RED%Invalid choice. Please select 1, 2, 3, or 4.%NC%
    timeout /t 2 >nul
    goto main
)

:: Ask date
:ask_date
echo.
set /p use_today=Do you want to use today's date? (Y/N): 
if /i "%use_today%"=="Y" goto run_script
if /i "%use_today%"=="N" goto date_prompt

echo %RED%Please enter Y or N%NC%
goto ask_date

:date_prompt
echo.
echo %YELLOW%You can type 'today' to use today's date instead.%NC%
:ask_custom_date
set /p custom_date=Enter custom date (YYYY-MM-DD): 
if /i "%custom_date%"=="today" goto run_script

echo %custom_date% | findstr /r "^[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]$" >nul
if errorlevel 1 (
    echo %RED%Invalid date format. Please try again or type 'today'%NC%
    goto ask_custom_date
)

:: Final command with custom date
set command=python "%DOWNLOADED_SCRIPT%" %mode% --date=%custom_date% --scrape-dir="%TEMP_SCRAPE%" --output-dir="%OUTPUT_DIR%"
goto run_confirm

:run_script
:: Final command with today's date
set command=python "%DOWNLOADED_SCRIPT%" %mode% --scrape-dir="%TEMP_SCRAPE%" --output-dir="%OUTPUT_DIR%"

:run_confirm
echo.
echo %CYAN%==============================================================%NC%
echo %YELLOW%Running:%NC% %command%
echo %CYAN%==============================================================%NC%

:: Create necessary directories
if not exist "%TEMP_SCRAPE%" mkdir "%TEMP_SCRAPE%"

:: Step 1: Ensure Python is available
where python >nul 2>&1 || (
    echo %RED%❌ Python not found. Please install Python and try again.%NC%
    pause
    exit /b
)

:: Step 2: Ensure required Python packages are installed
echo %CYAN%Checking Python requirements...%NC%
python -c "import pandas, requests, dateutil.parser, openpyxl" 2>nul || (
    echo %YELLOW%Installing required Python packages...%NC%
    python -m pip install pandas requests python-dateutil openpyxl >nul 2>&1
)

:: Step 3: Download latest Python script
echo %CYAN%Downloading latest script from GitHub...%NC%
powershell -Command "Invoke-WebRequest -Uri '%PY_SCRIPT_URL%' -OutFile '%DOWNLOADED_SCRIPT%'" >nul 2>&1

if not exist "%DOWNLOADED_SCRIPT%" (
    echo %RED%❌ Failed to download script.py from GitHub.%NC%
    pause
    goto main
)

:: Step 4: Run script
%command%
if %errorlevel% neq 0 (
    echo.
    echo %RED%❌ Script exited with an error.%NC%
    goto cleanup
)

echo.
echo %GREEN%✓ Script completed successfully.%NC%

:cleanup
echo %YELLOW%Cleaning up temporary scrape files...%NC%
rd /s /q "%TEMP_SCRAPE%" 2>nul

echo.
echo %CYAN%Press any key to return to the main menu...%NC%
pause >nul
goto main

:end
echo.
echo %GREEN%Goodbye!%NC%
exit /b

:banner
echo %BLUE%
echo.████████╗██████╗░██╗░█████╗░██╗░░██╗███╗░░██╗███╗░░██╗███████╗██████╗░
echo.╚══██╔══╝██╔══██╗██║██╔══██╗██║░██╔╝████╗░██║████╗░██║██╔════╝██╔══██╗
echo.░░░██║░░░██████╔╝██║██║░░╚═╝█████═╝░██╔██╗██║██╔██╗██║█████╗░░██████╔╝
echo.░░░██║░░░██╔═══╝░██║██║░░██╗██╔═██╗░██║╚████║██║╚████║██╔══╝░░██╔══██╗
echo.░░░██║░░░██║░░░░░██║╚█████╔╝██║░╚██╗██║░╚███║██║░╚███║███████╗██║░░██║
echo.░░░╚═╝░░░╚═╝░░░░░╚═╝░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝
echo.     [1;36mTricky Nepse – Analyze NEPSE Trends Like a Pro![0m
echo.
exit /b

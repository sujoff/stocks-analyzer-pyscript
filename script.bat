@echo off
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
chcp 65001 >nul

:: Define ANSI colors
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "MAGENTA=[35m"
set "CYAN=[36m"
set "WHITE=[37m"
set "NC=[0m"

:: Define directories
set "TEMP_SCRAPE=%TEMP%\Scrape-StockPrice"
set "OUTPUT_DIR=%TEMP%\Scraped-Excels"
set "PY_SCRIPT_URL=https://raw.githubusercontent.com/sujoff/stocks-analyzer-pyscript/refs/heads/main/script.py"
set "DOWNLOADED_SCRIPT=%TEMP%\script.py"

:main
cls
:: Get terminal width for centering
for /f %%W in ('powershell -command "$Host.UI.RawUI.WindowSize.Width"') do set "WIDTH=%%W"

call :center "%CYAN%==============================================================%NC%"
call :center "%MAGENTA%TRICKY NEPSE - STOCK MARKET ANALYZER%NC%"
call :center "%CYAN%==============================================================%NC%"
echo.
call :center "%YELLOW%Select scraping mode:%NC%"
call :center " [%CYAN%1%NC%] Daily"
call :center " [%CYAN%2%NC%] Weekly"
call :center " [%CYAN%3%NC%] Monthly"
call :center " [%CYAN%4%NC%] Exit"
echo.

set "mode_choice="
set /p mode_choice=Enter choice (1/2/3/4): 

if "%mode_choice%"=="4" goto end
if "%mode_choice%"=="1" set mode=--daily
if "%mode_choice%"=="2" set mode=--weekly
if "%mode_choice%"=="3" set mode=--monthly

if not defined mode (
    echo.
    call :center "%RED%Invalid choice. Please select 1, 2, 3, or 4.%NC%"
    timeout /t 2 >nul
    goto main
)

:ask_date
echo.
call :center "%YELLOW%Select Date Option:%NC%"
call :center " [%CYAN%1%NC%] Today"
call :center " [%CYAN%2%NC%] Yesterday"
call :center " [%CYAN%3%NC%] Custom Date"
echo.
set /p date_choice=%WHITE%Enter choice (1/2/3): %NC%

if "%date_choice%"=="1" goto run_script
if "%date_choice%"=="2" goto set_yesterday
if "%date_choice%"=="3" goto date_prompt

echo.
call :center "%RED%Please enter 1, 2, or 3%NC%"
goto ask_date

:set_yesterday
for /f "tokens=*" %%a in ('powershell -Command "Get-Date (Get-Date).AddDays(-1) -Format 'yyyy-MM-dd'"') do set "custom_date=%%a"
echo.
call :center "%GREEN%Selected Yesterday: %custom_date%%NC%"
goto run_with_date

:date_prompt
echo.
call :center "%YELLOW%Hint: You can type 'today' to use today's date.%NC%"
:ask_custom_date
set /p custom_date=%WHITE%Enter custom date (YYYY-MM-DD): %NC%
if /i "%custom_date%"=="today" goto run_script

echo %custom_date%| findstr /r "^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$" >nul
if errorlevel 1 (
    call :center "%RED%Invalid date format. Please try again.%NC%"
    goto ask_custom_date
)

:run_with_date
set command=python "%DOWNLOADED_SCRIPT%" %mode% --date=%custom_date% --scrape-dir="%TEMP_SCRAPE%" --output-dir="%OUTPUT_DIR%"
goto run_confirm

:run_script
set command=python "%DOWNLOADED_SCRIPT%" %mode% --scrape-dir="%TEMP_SCRAPE%" --output-dir="%OUTPUT_DIR%"

:run_confirm
echo.
call :center "%CYAN%==============================================================%NC%"
call :center "%GREEN% INITIALIZING:%NC% %WHITE%Analysis Engine%NC%"
call :center "%CYAN%==============================================================%NC%"

:: Ensure directories exist before running 
if not exist "%TEMP_SCRAPE%" mkdir "%TEMP_SCRAPE%"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

where python >nul 2>&1 || (
    call :center "%RED%❌ Python not found. Please install Python and try again.%NC%"
    pause
    exit /b
)

echo.
call :center "%BLUE%[1/3]%NC% %CYAN%Checking Python environment...%NC%"
python -c "import pandas, requests, dateutil.parser, openpyxl" 2>nul || (
    call :center "%YELLOW%Installing required Python packages...%NC%"
    python -m pip install pandas requests python-dateutil openpyxl >nul 2>&1
)

call :center "%BLUE%[2/3]%NC% %CYAN%Fetching latest engine from GitHub...%NC%"
powershell -Command "Invoke-WebRequest -Uri '%PY_SCRIPT_URL%' -OutFile '%DOWNLOADED_SCRIPT%'" >nul 2>&1

if not exist "%DOWNLOADED_SCRIPT%" (
    call :center "%RED%❌ Failed to download engine.%NC%"
    pause
    goto main
)

call :center "%BLUE%[3/3]%NC% %GREEN%Executing analysis...%NC%"
echo.
%command%

if %errorlevel% neq 0 (
    echo.
    call :center "%RED%❌ Script exited with an error.%NC%"
    goto cleanup
)

echo.
call :center "%GREEN%✔ Script completed successfully!%NC%"
call :center "%CYAN%Files saved to: %WHITE%%OUTPUT_DIR%%NC%"

:cleanup
echo.
call :center "%YELLOW%Cleaning up temporary files...%NC%"
rd /s /q "%TEMP_SCRAPE%" 2>nul

echo.
call :center "%CYAN%Press any key to return to the main menu...%NC%"
pause >nul
goto main

:end
echo.
call :center "%MAGENTA%Goodbye!%NC%"
timeout /t 2 >nul
exit /b

:center
set "text=%~1"
set "plain_text=%text:[31m=%"
set "plain_text=%plain_text:[32m=%"
set "plain_text=%plain_text:[33m=%"
set "plain_text=%plain_text:[34m=%"
set "plain_text=%plain_text:[35m=%"
set "plain_text=%plain_text:[36m=%"
set "plain_text=%plain_text:[37m=%"
set "plain_text=%plain_text:[0m=%"
set "length=0"
set "str=%plain_text%"
:len_loop
if not "%str%"=="" (
    set "str=%str:~1%"
    set /a length+=1
    goto len_loop
)
set /a "indent=(%WIDTH% - %length%) / 2"
set "line="
for /l %%i in (1,1,%indent%) do set "line=!line! "
echo !line!%text%
exit /b
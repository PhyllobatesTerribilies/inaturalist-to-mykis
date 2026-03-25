@echo off
setlocal EnableDelayedExpansion

echo ================================================
echo iNaturalist to Mykis - BEST PRACTICE BUILD
echo ================================================
echo.

REM === Python-Check ===
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden!
    pause
    exit /b 1
)

REM === Virtuelle Umgebung ===
if exist venv\Scripts\activate.bat (
    echo [1/4] Aktiviere venv...
    call venv\Scripts\activate.bat
)

REM === Dependencies ===
echo.
echo [2/4] Installiere Dependencies...
python -m pip install --quiet --upgrade
python -m pip install -r requirements.txt

REM === Cleanup ===
echo.
echo [3/4] Bereite Build vor...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM === Icon ===
set ICON_SWITCH=
if exist app.ico set ICON_SWITCH=--icon=app.ico

REM === BUILD ===
echo.
echo [4/4] Baue EXE...
echo.

pyinstaller ^
    --name=inaturalist-to-mykis ^
    --onedir ^
    --noconsole ^
	--add-data "assets;assets" ^
	--icon=assets/app.ico ^
    %ICON_SWITCH% ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=geopandas ^
    --hidden-import=pyogrio ^
    --hidden-import=pyogrio._geometry ^
    --collect-all=openpyxl ^
    --collect-all=geopandas ^
    --collect-all=pyogrio ^
    --clean ^
    app.py

if errorlevel 1 (
    echo.
    echo FEHLER beim Bauen!
    pause
    exit /b 1
)

echo.
echo ================================================
echo FERTIG!
echo ================================================
echo.
echo EXE: dist\inaturalist-to-mykis\inaturalist-to-mykis.exe 
dir "dist\inaturalist-to-mykis\inaturalist-to-mykis.exe" | find "inaturalist"
echo.
echo WICHTIG: src/ ist automatisch als Package eingebunden!
echo.
pause

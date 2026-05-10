@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

title AMAZON ADS PIPELINE - TEST 4

echo ============================================================
echo   STARTING FULL PIPELINE - TEST 4
echo ============================================================

set PYTHON_EXE=f:\Minhpython\venv\Scripts\python.exe

:: Kiem tra file python co ton tai khong
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Khong tim thay Python tai: %PYTHON_EXE%
    echo Vui long kiem tra lai duong dan venv.
    pause
    exit /b
)

:: Kiem tra xem co file Excel nao trong phase_bo_sung\input khong
if not exist "phase_bo_sung\input\*.xlsx" (
    echo ============================================================
    echo [ERROR] MISSING INPUT DATA!
    echo No Excel file found in: 
    echo f:\Minhpython\Test4\phase_bo_sung\input\
    echo.
    echo Please copy your Amazon Bulk report .xlsx into that folder.
    echo ============================================================
    pause
    exit /b
)


echo [PHASE BO SUNG] Splitting Bulk sheets...
"%PYTHON_EXE%" phase_bo_sung\code\split_bulk_sheets.py

echo [PHASE 0] Normalizing SP data...
"%PYTHON_EXE%" phase0\code\normalize_sp_campaigns.py

echo [PHASE 1] Classifying campaigns...
"%PYTHON_EXE%" phase1\code\1_split_campaigns.py
"%PYTHON_EXE%" phase1\code\2_classify_seasonal.py
"%PYTHON_EXE%" phase1\code\3_classify_evergreen.py

echo [PHASE 2] Aggregating performance metrics...
"%PYTHON_EXE%" phase2\code\phase2a_evergreen.py
"%PYTHON_EXE%" phase2\code\phase2b_seasonal.py

echo [PHASE 3] Analyzing Rules...
echo   - Evergreen Rules...
"%PYTHON_EXE%" phase3\code\apply_evergreen_rule\1_launch_rules.py
"%PYTHON_EXE%" phase3\code\apply_evergreen_rule\2_growth_rules.py
"%PYTHON_EXE%" phase3\code\apply_evergreen_rule\3_mature_rules.py
"%PYTHON_EXE%" phase3\code\apply_evergreen_rule\4_dormant_rules.py
echo   - Seasonal Rules...
"%PYTHON_EXE%" phase3\code\apply_seasonal_rule\1_pre_season_rules.py
"%PYTHON_EXE%" phase3\code\apply_seasonal_rule\2_peak_season_rules.py
"%PYTHON_EXE%" phase3\code\apply_seasonal_rule\3_post_season_rules.py

echo [PHASE 4] Generating Review Dashboard...
"%PYTHON_EXE%" phase4\code\4_generate_review_dashboard.py

echo.
echo ============================================================
echo   ACTION REQUIRED: Please check the Dashboard at:
echo   phase4\output\Action_Required_Dashboard.xlsx
echo   After review, press any key to continue...
echo ============================================================
pause

echo [PHASE 5] Generating Amazon Upload file...
"%PYTHON_EXE%" phase5\code\5_generate_bulk_upload.py

echo [PHASE 6] Validating IDs and Format (Customs)...
"%PYTHON_EXE%" phase6\code\6_validate_upload.py

echo ============================================================
echo   PIPELINE COMPLETE!
echo   Final file at: phase6\output\Amazon_Upload_Verified_*.xlsx
echo ============================================================
pause

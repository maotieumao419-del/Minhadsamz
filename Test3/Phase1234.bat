@echo off
echo =========================================================
echo   PIPELINE TU DONG: PHASE 0 - 1 - 2 - 3 - 4
echo =========================================================

call "f:\Minhpython\venv\Scripts\activate.bat"

echo.
echo -- PHASE 0: Chuan hoa du lieu Ghi chu (Match Type, Bid, Placement) --
python "%~dp0phase0\code\normalize_ghi_chu.py"
if %errorlevel% neq 0 ( echo [LOI] Phase 0 that bai! & pause & exit /b 1 )

echo.
REM echo -- PHASE 1a: Ket noi Supabase, tai du lieu --
REM python "%~dp0phase1\code\read_supabase.py"
REM if %errorlevel% neq 0 ( echo [LOI] Phase 1a that bai! & pause & exit /b 1 )

echo.
echo -- PHASE 1b: Loc SKU trang thai "Tiep nhan" --
python "%~dp0phase1\code\filter_sku.py"
if %errorlevel% neq 0 ( echo [LOI] Phase 1b that bai! & pause & exit /b 1 )

echo.
echo -- PHASE 2a: Doi chieu va copy file JSON (tu Phase 0 output) --
python "%~dp0phase2\code\match_sku_files.py"
if %errorlevel% neq 0 ( echo [LOI] Phase 2a that bai! & pause & exit /b 1 )

echo.
echo -- PHASE 2b: Chuyen tiep du lieu sang Phase 3 --
python "%~dp0phase2\code\transfer_to_phase3.py"
if %errorlevel% neq 0 ( echo [LOI] Phase 2b that bai! & pause & exit /b 1 )

echo.
echo -- PHASE 3: Dat ten Campaign + gan Match Type, Placement --
python "%~dp0phase3\code\process_phase3.py"
if %errorlevel% neq 0 ( echo [LOI] Phase 3 that bai! & pause & exit /b 1 )

echo.
echo -- PHASE 4: Xuat Excel Bulk Amazon Template --
python "%~dp0phase4\code\process_phase4.py"
if %errorlevel% neq 0 ( echo [LOI] Phase 4 that bai! & pause & exit /b 1 )

echo.
echo -- PHASE 5: Kiem tra loi (Validate) Excel Output --
python "%~dp0phase5\code\validate_excel.py"
if %errorlevel% neq 0 ( echo [LOI] Phase 5 that bai! & pause & exit /b 1 )

echo.
echo =========================================================
echo   HOAN TAT! Tat ca Phase 0-1-2-3-4-5 da chay thanh cong.
echo   Kiem tra file Bulk tai: phase4\output\
echo   Kiem tra bao cao loi tai: phase5\output\Validation_Report.txt
echo =========================================================
pause

@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo ============================================================
echo   CLEANING PROJECT DATA - TEST 4
echo ============================================================

set BASE_DIR=%~dp0

:: List of folders to clean. 
set FOLDERS=phase_bo_sung\input phase_bo_sung\output phase0\output phase1\output phase2\output phase3\output phase4\output phase5\output phase6\output


for %%f in (%FOLDERS%) do (
    set TARGET_DIR=%BASE_DIR%%%f
    if exist "!TARGET_DIR!" (
        echo [OK] Cleaning: %%f
        del /s /q "!TARGET_DIR!\*" > nul 2>&1
        for /d %%d in ("!TARGET_DIR!\*") do rd /s /q "%%d" > nul 2>&1
    ) else (
        echo [SKIP] Not found: %%f
    )
)

echo ============================================================
echo   CLEANING COMPLETE!
echo   (Your raw files in phase_bo_sung\input are kept safe)
echo ============================================================
pause

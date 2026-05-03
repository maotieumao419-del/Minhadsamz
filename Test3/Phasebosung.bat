@echo off
echo =========================================================
echo   PHASE BO SUNG - Boc tach Excel nhieu sheet ra JSON
echo =========================================================
echo.

call "f:\Minhpython\venv\Scripts\activate.bat"
python "%~dp0phase_bo_sung\code\convert_multisheet.py"

echo.
echo =========================================================
echo   PHASE BO SUNG HOAN TAT
echo =========================================================
pause

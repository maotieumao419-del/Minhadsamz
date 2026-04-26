@echo off
echo =========================================================
echo   CLEAN ALL - Xoa du lieu input/output de chay lai
echo =========================================================
echo.
echo   [!] File goc phase_bo_sung\input\ se KHONG bi xoa
echo.
echo   Nhan phim bat ky de tiep tuc. Nhan Ctrl+C de huy.
pause >nul

echo.
echo -- Xoa Phase Bo Sung: output --
del /q "%~dp0phase_bo_sung\output\*.json" 2>nul
echo    OK

echo.
echo -- Xoa Phase 1: output --
del /q "%~dp0phase1\output\*.json" 2>nul
del /q "%~dp0phase1\output\*.xlsx" 2>nul
echo    OK

echo.
echo -- Xoa Phase 2: input + output --
del /q "%~dp0phase2\input\*.json" 2>nul
del /q "%~dp0phase2\output\*.json" 2>nul
echo    OK

echo.
echo -- Xoa Phase 3: input + output --
del /q "%~dp0phase3\input\*.json" 2>nul
del /q "%~dp0phase3\output\*.json" 2>nul
echo    OK

echo.
echo -- Xoa Phase 4: input + output --
del /q "%~dp0phase4\input\*.json" 2>nul
del /q "%~dp0phase4\input\*.xlsx" 2>nul
del /q "%~dp0phase4\output\*.xlsx" 2>nul
echo    OK

echo.
echo =========================================================
echo   HOAN TAT! San sang chay lai pipeline.
echo   Buoc tiep: Phasebosung.bat -^> Phase1234.bat
echo =========================================================
pause

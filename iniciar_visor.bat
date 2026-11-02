@echo off
REM Arranca el visor del Imperio Espanol 1794 (doble clic en Windows)
cd /d "%~dp0"
where py >nul 2>nul && (py server.py & goto :fin)
where python >nul 2>nul && (python server.py & goto :fin)
echo.
echo  No se encuentra Python. Instalalo desde https://www.python.org/downloads/
echo  y marca la casilla "Add python.exe to PATH" durante la instalacion.
echo.
:fin
pause

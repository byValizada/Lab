@echo off
chcp 65001 >nul
cd /d "%~dp0"
title IT Laboratoriyasi - 3D Dizayner

echo.
echo   IT Laboratoriyasi - 3D Dizayner
echo   ================================
echo.

rem --- Port artiq mesguldursa, serveri tekrar qaldirmiriq ---
netstat -ano | findstr /r /c:":8123 .*LISTENING" >nul 2>nul
if %errorlevel%==0 (
    echo   Server artiq isleyir.
    goto OPEN
)

where python >nul 2>nul
if %errorlevel% neq 0 goto NOPYTHON

echo   Lokal server basladilir ^(port 8123^)...
start "lab3d-server" /min cmd /c "python -m http.server 8123"

rem --- Serverin qalxmasini gozleyirik (maks. 10 saniye) ---
set /a tries=0
:WAIT
set /a tries+=1
timeout /t 1 /nobreak >nul
netstat -ano | findstr /r /c:":8123 .*LISTENING" >nul 2>nul
if %errorlevel%==0 goto OPEN
if %tries% lss 10 goto WAIT

echo   Server qalxmadi. Fayl birbasa acilir...
start "" "%~dp0index.html"
goto DONE

:OPEN
start "" "http://localhost:8123"
echo.
echo   Brauzer acildi:  http://localhost:8123
echo.
echo   Isi bitirdikde "lab3d-server" penceresini baglayin.
goto DONE

:NOPYTHON
echo   Python tapilmadi - fayl birbasa acilir.
start "" "%~dp0index.html"

:DONE
echo.
pause

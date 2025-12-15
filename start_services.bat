@echo off
REM Script di avvio servizi per Windows
REM Sistema Gestione Ritiri con OR-Tools

echo ======================================================================
echo     Sistema Gestione Ritiri con OR-Tools
echo ======================================================================
echo.

REM Verifica Python installato
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato! Installa Python 3.8+ da python.org
    pause
    exit /b 1
)

echo [OK] Python trovato
echo.

REM Verifica dipendenze
echo Verifica dipendenze Python...
python -c "import ortools" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installazione dipendenze...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERRORE] Impossibile installare dipendenze
        pause
        exit /b 1
    )
)
echo [OK] Dipendenze installate
echo.

REM Kill processi esistenti
echo Terminazione processi esistenti...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq api.py*" >nul 2>&1
timeout /t 2 /nobreak >nul

REM Avvia API Backend
echo Avvio API Backend (porta 5000)...
start "OR-Tools API Backend" cmd /k python api.py
timeout /t 4 /nobreak >nul

REM Verifica API
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] API Backend non risponde
    echo Controlla la finestra "OR-Tools API Backend"
    pause
    exit /b 1
)
echo [OK] API Backend attiva
echo.

REM Avvia Frontend
echo Avvio Frontend (porta 8000)...
start "Frontend HTTP Server" cmd /k python -m http.server 8000
timeout /t 3 /nobreak >nul

REM Verifica Frontend
curl -s http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Frontend non risponde
    echo Controlla la finestra "Frontend HTTP Server"
    pause
    exit /b 1
)
echo [OK] Frontend attivo
echo.

REM Riepilogo
echo ======================================================================
echo [SUCCESS] Tutti i servizi sono attivi!
echo ======================================================================
echo.
echo URL Servizi:
echo    Frontend:     http://localhost:8000
echo    API Backend:  http://localhost:5000
echo    Health Check: http://localhost:5000/health
echo.
echo Premi un tasto per aprire il browser...
pause >nul

REM Apri browser
start http://localhost:8000

echo.
echo ======================================================================
echo Sistema pronto all'uso!
echo ======================================================================
echo.
echo Per fermare i servizi chiudi le finestre:
echo    - OR-Tools API Backend
echo    - Frontend HTTP Server
echo.
pause

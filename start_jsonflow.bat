@echo off
chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION
set PYTHONUTF8=1

title JsonFlow – API FastAPI Starter

echo =====================================================
echo 🚀 Lancement de JsonFlow – API FastAPI pour robot modulaire
echo =====================================================
echo.

REM === Vérifie la présence de Python ===
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ❌ Python n'est pas installé ou non trouvé dans le PATH.
    echo    Installez Python 3.10+ avant d'exécuter ce script.
    pause
    exit /b
)

REM === Vérifie si l'environnement virtuel existe ===
IF NOT EXIST ".venv\" (
    echo 🔧 Création de l'environnement virtuel...
    python -m venv .venv
    IF ERRORLEVEL 1 (
        echo ❌ Erreur lors de la création du venv.
        pause
        exit /b
    )

    echo 📦 Installation des dépendances...
    call .venv\Scripts\activate
    python -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
) ELSE (
    echo ✅ Environnement virtuel détecté.
)

REM === Active l'environnement virtuel ===
echo 🟢 Activation de l'environnement virtuel...
call .venv\Scripts\activate

REM === Démarre le serveur FastAPI dans une nouvelle console ===
echo 🚀 Démarrage du serveur FastAPI...
start "JsonFlow – API Server" cmd /k ".venv\Scripts\python.exe -m uvicorn jsonflow_api.main:app --reload"

REM === Attente que le serveur soit prêt ===
echo 🕒 Vérification que le serveur répond avant exécution du client et génération du README_JSONFLOW...
set RETRIES=15
set COUNT=0

:WAIT_LOOP
set /A COUNT+=1
for /f %%i in ('powershell -Command "(Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/markdown-docs' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty StatusCode)"') do set STATUS=%%i

if "%STATUS%"=="200" (
    echo ✅ Serveur prêt !
    goto SERVER_READY
)

if %COUNT% GEQ %RETRIES% (
    echo ⚠️ Le serveur n'a pas répondu à temps. Client et README_JSONFLOW.md non exécutés.
    goto END
)

timeout /t 1 >nul
goto WAIT_LOOP

:SERVER_READY
REM === Démarre le client REST dans une autre console ===
IF EXIST "client\client_rest.py" (
    echo 🧪 Exécution du client REST...
    start "JsonFlow – Client REST" cmd /k ".venv\Scripts\python.exe client\client_rest.py"
) ELSE (
    echo ⚠️ Aucun client REST trouvé dans client\client_rest.py
)

echo.
echo =====================================================
echo ✅ API JsonFlow en cours d’exécution sur http://127.0.0.1:8000
echo =====================================================

:END
pause
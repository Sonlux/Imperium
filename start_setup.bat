@echo off
REM Imperium Project Complete Setup Script
REM Creates all directories and runs Python deployment

echo ============================================================
echo Imperium Project Setup
echo ============================================================
echo.

cd /d "%~dp0"

echo Creating directory structure...
mkdir src\intent_manager 2>nul
mkdir src\policy_engine 2>nul
mkdir src\enforcement 2>nul
mkdir src\feedback 2>nul
mkdir src\iot_simulator 2>nul
mkdir config 2>nul
mkdir monitoring\prometheus 2>nul
mkdir monitoring\grafana\provisioning\datasources 2>nul
mkdir monitoring\grafana\provisioning\dashboards 2>nul
mkdir scripts 2>nul
mkdir tests 2>nul

echo.
echo Running Python deployment script...
python deploy.py

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo To start the project:
echo   1. pip install -r requirements.txt
echo   2. docker-compose up -d
echo   3. python src\intent_manager\api.py
echo.
pause

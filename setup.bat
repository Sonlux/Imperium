@echo off
echo Creating Imperium Project Structure...
echo.

REM Create main directories
mkdir src\intent_manager 2>nul
mkdir src\policy_engine 2>nul
mkdir src\enforcement 2>nul
mkdir src\feedback 2>nul
mkdir src\iot_simulator 2>nul
mkdir config 2>nul
mkdir monitoring\prometheus 2>nul
mkdir monitoring\grafana\provisioning 2>nul
mkdir scripts 2>nul
mkdir tests 2>nul

echo Directory structure created!
echo.

REM Create Python package __init__ files
echo """Intent Manager Package""" > src\intent_manager\__init__.py
echo """Policy Engine Package""" > src\policy_engine\__init__.py
echo """Enforcement Package""" > src\enforcement\__init__.py
echo """Feedback Loop Package""" > src\feedback\__init__.py
echo """IoT Simulator Package""" > src\iot_simulator\__init__.py

echo Python packages initialized!
echo.

REM Run Python setup if available
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python found! Running setup_structure.py...
    python setup_structure.py
) else (
    echo Python not found in PATH. Please install Python 3.8+ to continue.
)

echo.
echo Setup complete! Project structure is ready.
pause

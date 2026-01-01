@echo off
REM Final commit of all implementation files
echo ============================================================
echo Committing implementation files to main
echo ============================================================
echo.

cd /d "%~dp0"

echo Current branch:
git branch
echo.

echo Adding all new files...
git add .

echo.
echo Committing...
git commit -m "Complete core implementation: Intent Manager, Policy Engine, Enforcement, Feedback Loop, IoT Simulator, and tests"

echo.
echo ============================================================
echo Implementation committed successfully!
echo ============================================================
echo.

echo Files committed:
git log --oneline -1 --stat
echo.

echo To push to remote:
echo   git push origin main
echo.
pause

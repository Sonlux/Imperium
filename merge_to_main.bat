@echo off
REM Merge worktree branch into main and clean up
echo ============================================================
echo Merging to main branch and cleaning up worktree
echo ============================================================
echo.

cd /d "%~dp0"

echo Current branch status:
git branch
echo.

echo Switching to main branch...
git checkout main
echo.

echo Merging worktree branch into main...
git merge worktree-2026-01-01T12-37-05 --no-ff -m "Merge: Initial implementation complete"
echo.

echo ============================================================
echo Merge completed successfully!
echo ============================================================
echo.

echo Current branch (should be main):
git branch
echo.

echo Files in main branch:
git log --oneline -5
echo.

echo To push to remote:
echo   git push origin main
echo.
echo To delete the worktree branch (optional):
echo   git branch -d worktree-2026-01-01T12-37-05
echo.
pause

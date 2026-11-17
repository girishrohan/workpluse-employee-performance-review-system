@echo off
:: ==============================================================================
:: WorkPulse - Employee Performance Review System Deployment Script
:: Windows-compatible deployment script for GitHub + Streamlit Community Cloud
:: ==============================================================================

set SCRIPT_DIR=%~dp0
pushd %SCRIPT_DIR%

echo.
echo ============================================================================
echo WorkPulse Deployment Script
echo ============================================================================

:: 1. Check Git status
echo.
echo [1/7] Checking Git status...
git status

if errorlevel 1 (
    echo Warning: git status returned errors.
    pause
    popd
    exit /b 1
)

:: 2. Display modified files
echo.
echo [2/7] Displaying modified/new files...
git diff --name-only
git diff --cached --name-only
git status --porcelain

:: 3. Stage required changes
echo.
echo [3/7] Staging changes...
echo Add required files? (y/n)
set /p answer=

if /i "%answer%" == "y" (
    :: Stage all modified and new tracked files (exclude untracked .claude/ unless intended)
    git add .
    echo Files staged successfully.
) else (
    echo Which files to stage? Provide space-separated paths or patterns.
    set /p files=
    if not "%files%"=="" (
        git add %files%
        echo Selected files staged.
    ) else (
        echo No files staged.
    )
)

:: 4. Ask for commit message
echo.
echo [4/7] Enter commit message (press Enter to skip commit, or type message and press Enter):
set /p commitMessage=

if "%commitMessage%"=="" (
    echo Skipping commit.
    set COMMIT_DONE=0
) else (
    git commit -m "%commitMessage%"
    echo Commit created successfully.
    set COMMIT_DONE=1
)

:: 5. Push to GitHub
echo.
echo [5/7] Pushing to GitHub origin/main...
git push origin main

if errorlevel 1 (
    echo.
    echo ERROR: Git push failed.
    echo Please resolve the following:
    echo - Ensure you are on the main branch: git branch
    echo - Pull latest changes: git pull origin main
    echo - Check GitHub authentication
    pause
    popd
    exit /b 1
) else (
    echo Push successful!
    set PUSH_DONE=1
)

:: 6. Summary
echo.
echo ============================================================================
echo [6/7] Deployment Summary
echo ============================================================================
echo Git status:
git status
echo.
echo Commit: %COMMIT_DONE%
echo Push: %PUSH_DONE%
echo.
echo Please verify:
echo - Changes are on GitHub: https://github.com/girishrohan/workpluse-employee-performance-review-system
echo - Streamlit Community Cloud: Check your deployment dashboard
echo.

:: 7. Local development instructions
echo ============================================================================
echo [7/7] Local Development
echo ============================================================================
echo To run locally:
echo   streamlit run app.py
echo.
echo Port configuration (from .claude/launch.json):
echo   Default: 8510 (configured in this project)
echo   Alternative: 8501, 8502, etc.
echo.
echo Authentication credentials (first-run defaults):
echo   Admin: admin@workpulse.local / Admin@WorkPulse2024
echo   HR:    hr@workpulse.local / Hr@WorkPulse2024
echo   Employee: employee@workpulse.local / Emp@WorkPulse2024
echo.
echo Required environment variables for production:
echo   - Copy .env.example to .env and fill in Supabase credentials
echo   - Set SECRET_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
echo   - DATABASE_PROVIDER=sqlite (local) or supabase (cloud)
echo.
echo Deployment notes:
echo   - Streamlit Community Cloud auto-detects app.py as entry point
echo   - Ensure .env and .db files are in .gitignore (already configured)
echo   - No API keys or secrets in repository - use Streamlit secrets
echo   - Headless mode: .streamlit/config.toml has headless = true
echo.

popd
echo.
echo Deployment script completed.
echo ============================================================================
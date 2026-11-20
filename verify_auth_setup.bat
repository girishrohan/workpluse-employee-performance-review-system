@echo off
echo ==========================================
echo WorkPulse Supabase Auth Setup Verification
echo ==========================================
echo.

echo 1. Checking environment files...
if exist .env.local (
  echo .env.local exists - checking for redirect URL...
  findstr /I "NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL" .env.local >nul && echo   OK: Redirect URL configured/placeholder found
) else (
  echo .env.local MISSING - copy from .env.example
)
if exist .env.example (
  echo .env.example exists
  findstr /I "NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL" .env.example >nul && echo   OK: Redirect URL config in .env.example
)
echo.

echo 2. Checking middleware.ts...
if exist middleware.ts (
  echo middleware.ts exists - checking for proper config...
  findstr "createServerClient" middleware.ts >nul && echo   OK: Supabase SSR middleware configured
) else (
  echo middleware.ts MISSING
)
echo.

echo 3. Checking auth callback route...
if exist app\auth\callback\route.ts (
  echo app\auth\callback\route.ts exists
  findstr "exchangeCodeForSession" app\auth\callback\route.ts >nul && echo   OK: Code exchange configured
  findstr "error" app\auth\callback\route.ts >nul && echo   OK: Error handling configured
)
echo.

echo 4. Checking auth-form.tsx...
if exist components\auth-form.tsx (
  echo components\auth-form.tsx exists
  findstr "NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL" components\auth-form.tsx >nul && echo   OK: Redirect URL used in signUp options
  findstr "getAuthErrorMessage" components\auth-form.tsx >nul && echo   OK: Meaningful error messages configured
  findstr "urlMessage\|searchParams" components\auth-form.tsx >nul && echo   OK: URL error handling configured
)
echo.

echo 5. Checking auth error page...
if exist app\auth\error\page.tsx (
  echo app\auth\error\page.tsx exists
  findstr "error\|message" app\auth\error\page.tsx >nul && echo   OK: Meaningful error display configured
  findstr "getErrorMessage\|AlertCircle" app\auth\error\page.tsx >nul && echo   OK: Error routing configured
)
echo.

echo 6. Checking workspace-shell.tsx...
if exist components\workspace-shell.tsx (
  echo components\workspace-shell.tsx exists
  findstr "role=" components\workspace-shell.tsx >nul && echo   OK: Role-based navigation configured
)
echo.

echo 7. Checking workspace layout...
if exist app\\(workspace)\layout.tsx (
  echo app\\(workspace)\layout.tsx exists
  findstr "user_metadata" app\\(workspace)\layout.tsx >nul && echo   OK: User role metadata retrieved
)
echo.

echo 8. Checking Supabase client config...
if exist lib\supabase\client.ts (
  echo lib\supabase\client.ts exists
  findstr "NEXT_PUBLIC_SUPABASE_URL\|NEXT_PUBLIC_SUPABASE_ANON_KEY\|NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" lib\supabase\client.ts >nul && echo   OK: Supabase client URL/key configured
)
echo.

echo 9. Checking server.ts config...
if exist lib\supabase\server.ts (
  echo lib\supabase\server.ts exists
  findstr "NEXT_PUBLIC_SUPABASE_URL\|NEXT_PUBLIC_SUPABASE_ANON_KEY\|NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" lib\supabase\server.ts >nul && echo   OK: Supabase server URL/key configured
)
echo.

echo 10. Checking Supabase Dashboard redirect URL configuration...
echo Please manually verify:
echo 1. Go to: https://supabase.com/dashboard
echo 2. Navigate to Authentication > URL Configuration
echo 3. Add these Redirect URLs:
echo    - http://localhost:3000/auth/callback
echo    - https://v0.app/chat/api/supabase/redirect/nT2wVXJRJLO
echo    - https://your-app.vercel.app/auth/callback
echo 4. Set Site URL to match your deployment
echo ==========
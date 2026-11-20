---
phase: 1
plan: 3
wave: 3
depends_on: ["1.1", "1.2"]
files_modified:
  - middleware.ts
  - app/(workspace)/layout.tsx
  - components/workspace-shell.tsx
  - components/workspace-user.tsx
  - components/auth-form.tsx
  - app/auth/login/page.tsx
  - app/auth/sign-up/page.tsx
  - app/auth/error/page.tsx (remove)
  - app/auth/callback/route.ts (remove)
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Middleware protects routes using custom session cookie"
    - "Workspace layout reads user from custom session"
    - "Login form posts to /api/auth/login"
    - "Sign-up form posts to /api/auth/register"
    - "Sign out calls /api/auth/logout"
    - "Role-based navigation works with custom auth"
  artifacts:
    - "Updated middleware.ts"
    - "Updated app/(workspace)/layout.tsx"
    - "Updated components/workspace-shell.tsx"
    - "Updated components/auth-form.tsx"
    - "Removed app/auth/callback/route.ts"
    - "Removed app/auth/error/page.tsx"
---

# Plan 1.3: Update Middleware & Frontend Components

## Objective
Replace Supabase Auth middleware and frontend components with custom auth equivalents.

Purpose: Wire the new auth system into the request lifecycle and UI.

Output: Updated middleware, layout, shell, auth form, and login/signup pages.

## Context
Load for context:
- middleware.ts (current Supabase Auth middleware)
- app/(workspace)/layout.tsx (current workspace layout)
- components/workspace-shell.tsx (current shell with Supabase signOut)
- components/auth-form.tsx (current form with Supabase client)
- app/auth/login/page.tsx, app/auth/sign-up/page.tsx
- lib/auth/session.ts (from Plan 1.1)

## Tasks

<task type="auto">
  <name>Update middleware for custom session auth</name>
  <files>middleware.ts</files>
  <action>
    Rewrite middleware to use custom session:
    - Import getSession from lib/auth/session (but middleware can't use async directly)
    - Alternative: Use iron-session directly in middleware with cookie parsing
    - Check for session cookie, verify JWT with jose
    - Protected paths: /dashboard, /employees, /cycles, /assessments, /settings
    - Auth paths: /auth/login, /auth/sign-up (redirect to /dashboard if authenticated)
    - Attach user info to request headers for Server Components
    
    AVOID: Using Supabase Auth getUser()
    AVOID: Complex async in middleware - keep it lightweight
    USE: jose JWT verification directly on cookie
  </action>
  <verify>Middleware redirects unauthenticated from protected routes; allows authenticated</verify>
  <done>middleware.ts uses custom JWT verification</done>
</task>

<task type="auto">
  <name>Update workspace layout for custom auth</name>
  <files>app/(workspace)/layout.tsx</files>
  <action>
    Update layout to use custom session:
    - Import getSession from lib/auth/session
    - Call getSession() to get current user
    - If no user: redirect to /auth/login
    - Pass user info (id, email, role, full_name) to WorkspaceShell
    
    AVOID: Supabase Auth getUser()
    AVOID: Supabase user_metadata - use users table role column
  </action>
  <verify>Layout redirects unauthenticated; passes user to shell</verify>
  <done>app/(workspace)/layout.tsx uses custom session</done>
</task>

<task type="auto">
  <name>Update workspace shell for custom signOut</name>
  <files>components/workspace-shell.tsx</files>
  <action>
    Update signOut function:
    - Call /api/auth/logout via fetch
    - Then router.replace('/auth/login') and router.refresh()
    - Remove Supabase client import and auth.signOut()
    - Keep role-based navigation logic (works with custom role)
    
    AVOID: Supabase auth.signOut()
  </action>
  <verify>Sign out button clears session and redirects to login</verify>
  <done>components/workspace-shell.tsx uses custom logout</done>
</task>

<task type="auto">
  <name>Update auth form for custom API endpoints</name>
  <files>components/auth-form.tsx</files>
  <action>
    Rewrite form submission to use custom endpoints:
    - Login: POST to /api/auth/login with { email, password }
    - Register: POST to /api/auth/register with { email, password, name }
    - Handle responses: success → router.push('/dashboard'), error → display message
    - Remove Supabase client import and all Supabase Auth calls
    - Keep error message formatting (adapt for custom error responses)
    - Keep UI/UX exactly the same
    
    AVOID: Supabase auth.signInWithPassword, auth.signUp
    AVOID: Email confirmation flow - direct login after register
  </action>
  <verify>Login form works with /api/auth/login; Register works with /api/auth/register</verify>
  <done>components/auth-form.tsx uses custom auth endpoints</done>
</task>

<task type="auto">
  <name>Remove Supabase Auth callback and error pages</name>
  <files>app/auth/callback/route.ts, app/auth/error/page.tsx</files>
  <action>
    Delete these files as they're no longer needed:
    - app/auth/callback/route.ts (Supabase OAuth callback)
    - app/auth/error/page.tsx (Supabase OAuth error page)
    
    AVOID: Keeping dead code
  </action>
  <verify>Files deleted; no references remain in codebase</verify>
  <done>Supabase Auth callback and error pages removed</done>
</task>

<task type="auto">
  <name>Update login and sign-up pages (minimal)</name>
  <files>app/auth/login/page.tsx, app/auth/sign-up/page.tsx</files>
  <action>
    These pages just render AuthForm - no changes needed unless we want to adjust.
    Verify they still work with updated AuthForm.
    
    AVOID: Unnecessary changes
  </action>
  <verify>Pages render correctly</verify>
  <done>Login and sign-up pages work with new AuthForm</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] Middleware protects routes correctly
- [ ] Workspace layout gets user from custom session
- [ ] Sign out works via /api/auth/logout
- [ ] Login form submits to /api/auth/login
- [ ] Sign-up form submits to /api/auth/register
- [ ] No Supabase Auth imports in any modified files
- [ ] Callback and error pages removed
</verification>

<success_criteria>
- [ ] All tasks verified
- [ ] Must-haves confirmed
</success_criteria>
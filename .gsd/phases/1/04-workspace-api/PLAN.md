---
phase: 1
plan: 4
wave: 4
depends_on: ["1.1", "1.2", "1.3"]
files_modified:
  - components/workspace-view.tsx
  - app/api/admin/seed/route.ts
  - lib/supabase/server.ts (verify)
  - lib/supabase/client.ts (verify)
  - .env.local (create from example)
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Workspace view fetches data without Supabase Auth user_id"
    - "Admin seed endpoint uses custom auth for admin check"
    - "All Supabase client usage is for database only"
    - "RLS policies work with custom JWT (or disabled for dev)"
  artifacts:
    - "Updated components/workspace-view.tsx"
    - "Updated app/api/admin/seed/route.ts"
    - ".env.local with AUTH_SECRET"
---

# Plan 1.4: Update Workspace View & API Routes

## Objective
Remove remaining Supabase Auth dependencies from workspace components and API routes.

Purpose: Ensure all data fetching and mutations work with custom auth system.

Output: Updated workspace view, admin seed endpoint, and verified Supabase clients.

## Context
Load for context:
- components/workspace-view.tsx (uses supabase.auth.getUser() for user_id)
- app/api/admin/seed/route.ts (uses supabase.auth.getUser() for admin check)
- lib/supabase/server.ts, lib/supabase/client.ts (updated in Plan 1.1)
- lib/auth/session.ts (for getting current user)

## Tasks

<task type="auto">
  <name>Update workspace view for custom auth</name>
  <files>components/workspace-view.tsx</files>
  <action>
    Replace Supabase Auth user_id with custom auth:
    - Remove supabase.auth.getUser() calls in saveEmployee, saveCycle, saveAssessment
    - Get user_id from useWorkspaceUserId() context (passed from WorkspaceShell)
    - The userId is already available from the custom session
    - Update employee insert to use the context userId instead of Supabase Auth
    - Keep all data fetching logic (RLS policies need adjustment - see note)
    
    AVOID: supabase.auth.getUser() - use context userId
    AVOID: Breaking existing data fetching - RLS may need service role for admin
    
    NOTE: For RLS to work with custom auth, either:
    1. Use service role key for admin operations (bypass RLS)
    2. Pass custom JWT to Supabase via Authorization header
    3. Disable RLS temporarily for development
  </action>
  <verify>Workspace view saves data without Supabase Auth calls</verify>
  <done>components/workspace-view.tsx uses context userId for mutations</done>
</task>

<task type="auto">
  <name>Update admin seed endpoint for custom auth</name>
  <files>app/api/admin/seed/route.ts</files>
  <action>
    Replace Supabase Auth admin check with custom session:
    - Import getSession from lib/auth/session
    - Call getSession() to get current user
    - Check user.role === 'admin' from session
    - Remove supabase.auth.getUser() and users table lookup
    - Keep all seeding logic the same
    
    AVOID: Supabase Auth getUser()
    AVOID: Users table lookup for role - use session role
  </action>
  <verify>Seed endpoint works with custom admin session</verify>
  <done>app/api/admin/seed/route.ts uses custom session for auth</done>
</task>

<task type="auto">
  <name>Verify Supabase clients are database-only</name>
  <files>lib/supabase/server.ts, lib/supabase/client.ts</files>
  <action>
    Confirm both clients:
    - Only import @supabase/supabase-js (not @supabase/ssr)
    - Create client with URL and anon/service key only
    - No cookie handling, no auth methods
    - Used purely for database queries
    
    AVOID: Any Supabase Auth method calls
  </action>
  <verify>No @supabase/ssr imports; no auth method usage</verify>
  <done>Supabase clients are database-only</done>
</task>

<task type="auto">
  <name>Create .env.local with required variables</name>
  <files>.env.local</files>
  <action>
    Create .env.local from .env.example with:
    - NEXT_PUBLIC_SUPABASE_URL (your Supabase project URL)
    - NEXT_PUBLIC_SUPABASE_ANON_KEY (your Supabase anon key)
    - AUTH_SECRET (generate 32+ char random string)
    - Optional: SUPABASE_SERVICE_ROLE_KEY for admin operations bypassing RLS
    
    AVOID: Committing real secrets to git
    AVOID: Using Supabase Auth redirect URLs
  </action>
  <verify>.env.local exists with all required vars</verify>
  <done>.env.local configured for custom auth</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] Workspace view mutations work with context userId
- [ ] Admin seed endpoint checks role from custom session
- [ ] Supabase clients have no auth code
- [ ] .env.local has AUTH_SECRET and Supabase DB credentials
- [ ] Full auth flow works: register → login → dashboard → logout
</verification>

<success_criteria>
- [ ] All tasks verified
- [ ] Must-haves confirmed
</success_criteria>
---
phase: 1
plan: 2
wave: 2
depends_on: ["1.1"]
files_modified:
  - app/api/auth/login/route.ts
  - app/api/auth/register/route.ts
  - app/api/auth/logout/route.ts
  - app/api/auth/me/route.ts
  - lib/auth/user.ts
  - sql/auth_schema.sql
autonomous: true
user_setup: []

must_haves:
  truths:
    - "POST /api/auth/login accepts email/password, returns session cookie"
    - "POST /api/auth/register creates user with hashed password"
    - "POST /api/auth/logout clears session cookie"
    - "GET /api/auth/me returns current user from session"
    - "Default admin user seeded with known credentials"
  artifacts:
    - "app/api/auth/login/route.ts"
    - "app/api/auth/register/route.ts"
    - "app/api/auth/logout/route.ts"
    - "app/api/auth/me/route.ts"
    - "lib/auth/user.ts - user database operations"
    - "sql/auth_schema.sql - migration to add password_hash to users table"
---

# Plan 1.2: Implement Auth API Endpoints

## Objective
Create standard email/password authentication API endpoints (login, register, logout, me) with proper session management.

Purpose: Replace Supabase Auth endpoints with custom auth flow.

Output: Four API routes and user database operations.

## Context
Load for context:
- lib/auth/types.ts, password.ts, jwt.ts, session.ts (from Plan 1.1)
- sql/supabase_schema.sql (existing users table structure)
- app/api/admin/seed/route.ts (reference for Supabase client usage)

## Tasks

<task type="auto">
  <name>Create user database operations</name>
  <files>lib/auth/user.ts</files>
  <action>
    Implement user CRUD operations using Supabase client:
    - createUser(email: string, passwordHash: string, role: string, fullName: string): Promise<User>
    - getUserByEmail(email: string): Promise<User | null>
    - getUserById(id: string): Promise<User | null>
    - updateUserRole(userId: string, role: string): Promise<void>
    
    Use the Supabase server client for database operations.
    Table: users (add password_hash column)
    Default admin: admin@workpulse.local with role='admin'
    
    AVOID: Supabase Auth methods - use direct database operations
    AVOID: Storing plain passwords
  </action>
  <verify>TypeScript compiles; functions export correctly</verify>
  <done>lib/auth/user.ts exports all user operations</done>
</task>

<task type="auto">
  <name>Create SQL migration for password_hash column</name>
  <files>sql/auth_schema.sql</files>
  <action>
    Create migration to add password_hash to users table:
    - ALTER TABLE users ADD COLUMN password_hash TEXT
    - Update RLS policies to work without Supabase Auth (use custom JWT)
    - Seed default admin user: admin@workpulse.local with bcrypt hash of 'Admin@WorkPulse2024'
    - Keep existing RLS policies but note they need custom JWT validation
    
    AVOID: Dropping existing data
    AVOID: Breaking existing RLS - policies will need adjustment for custom auth
  </action>
  <verify>SQL syntax valid; can run against Supabase</verify>
  <done>sql/auth_schema.sql adds password_hash and seeds admin</done>
</task>

<task type="auto">
  <name>Create login API endpoint</name>
  <files>app/api/auth/login/route.ts</files>
  <action>
    Implement POST /api/auth/login:
    - Accept { email, password } JSON body
    - Find user by email using getUserByEmail
    - Verify password with verifyPassword
    - On success: create session payload, setSession cookie, return { user: { id, email, role, full_name } }
    - On failure: return 401 with { error: 'Invalid credentials' }
    - Handle edge cases: missing fields, user not found, wrong password
    
    AVOID: Leaking whether email exists (use generic error)
    AVOID: Supabase Auth signInWithPassword
  </action>
  <verify>curl POST with valid creds returns 200 + Set-Cookie; invalid returns 401</verify>
  <done>app/api/auth/login/route.ts implements secure login</done>
</task>

<task type="auto">
  <name>Create register API endpoint</name>
  <files>app/api/auth/register/route.ts</files>
  <action>
    Implement POST /api/auth/register:
    - Accept { email, password, name } JSON body
    - Validate email format, password strength (min 8 chars)
    - Check if user already exists
    - Hash password with hashPassword
    - Create user with role='employee' (default)
    - Set session cookie, return user object
    - On failure: return 400/409 with appropriate error
    
    AVOID: Allowing duplicate emails
    AVOID: Weak password requirements
  </action>
  <verify>curl POST with valid data returns 201 + Set-Cookie; duplicate email returns 409</verify>
  <done>app/api/auth/register/route.ts implements secure registration</done>
</task>

<task type="auto">
  <name>Create logout API endpoint</name>
  <files>app/api/auth/logout/route.ts</files>
  <action>
    Implement POST /api/auth/logout:
    - Call clearSession to remove cookie
    - Return 200 with { success: true }
    
    AVOID: Requiring authentication to logout (should be idempotent)
  </action>
  <verify>curl POST returns 200 and clears cookie</verify>
  <done>app/api/auth/logout/route.ts clears session</done>
</task>

<task type="auto">
  <name>Create me API endpoint</name>
  <files>app/api/auth/me/route.ts</files>
  <action>
    Implement GET /api/auth/me:
    - Get session using getSession()
    - If valid session: fetch user by ID, return { user: { id, email, role, full_name, employee_code } }
    - If no/invalid session: return 401 with { error: 'Not authenticated' }
    
    AVOID: Returning password_hash
    AVOID: Supabase Auth getUser()
  </action>
  <verify>curl with valid cookie returns 200 + user; without returns 401</verify>
  <done>app/api/auth/me/route.ts returns current user from session</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] All 4 API routes exist and compile
- [ ] lib/auth/user.ts exports all operations
- [ ] sql/auth_schema.sql can be applied
- [ ] Login/register/logout/me flow works end-to-end
</verification>

<success_criteria>
- [ ] All tasks verified
- [ ] Must-haves confirmed
</success_criteria>
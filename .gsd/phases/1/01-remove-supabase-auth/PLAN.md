---
phase: 1
plan: 1
wave: 1
depends_on: []
files_modified:
  - package.json
  - lib/auth/password.ts
  - lib/auth/jwt.ts
  - lib/auth/session.ts
  - lib/auth/types.ts
  - lib/supabase/server.ts
  - lib/supabase/client.ts
  - middleware.ts
  - .env.example
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Supabase Auth SDK calls removed from all frontend/backend code"
    - "bcrypt password hashing available for password storage"
    - "JWT token generation/validation with jose library"
    - "Session cookie management utilities created"
  artifacts:
    - "package.json updated with bcrypt, jose, iron-session dependencies"
    - "lib/auth/password.ts - password hashing utilities"
    - "lib/auth/jwt.ts - JWT token utilities"
    - "lib/auth/session.ts - session cookie utilities"
    - "lib/auth/types.ts - auth type definitions"
    - ".env.example includes AUTH_SECRET and DATABASE_URL"
---

# Plan 1.1: Remove Supabase Auth Dependencies & Add Auth Primitives

## Objective
Remove Supabase Auth SDK dependencies and replace with standard auth primitives (bcrypt, JWT, session cookies). Keep Supabase client for database access only.

Purpose: Decouple authentication from Supabase Auth while maintaining database connectivity.

Output: New auth library files and updated package.json.

## Context
Load for context:
- package.json (current dependencies)
- lib/supabase/server.ts (Supabase server client)
- lib/supabase/client.ts (Supabase browser client)
- middleware.ts (current auth middleware)

## Tasks

<task type="auto">
  <name>Update package.json with new auth dependencies</name>
  <files>package.json</files>
  <action>
    Replace @supabase/ssr and @supabase/supabase-js with:
    - bcrypt (password hashing)
    - jose (JWT tokens - works in Edge runtime)
    - iron-session (session cookie management)
    - @types/bcrypt (types)
    Keep supabase-js for database access only (remove @supabase/ssr)
    
    AVOID: jsonwebtoken - it has CommonJS issues in Next.js Edge runtime
    AVOID: Keeping @supabase/ssr - it's tied to Supabase Auth
  </action>
  <verify>npm install succeeds and no @supabase/ssr in dependencies</verify>
  <done>package.json has bcrypt, jose, iron-session; @supabase/ssr removed; @supabase/supabase-js kept for DB</done>
</task>

<task type="auto">
  <name>Create auth type definitions</name>
  <files>lib/auth/types.ts</files>
  <action>
    Define TypeScript types for the new auth system:
    - User interface (id, email, role, full_name, employee_code, password_hash)
    - SessionPayload interface (userId, email, role, iat, exp)
    - AuthResult types for API responses
    - Role type ('admin' | 'hr' | 'employee')
    
    These types will be used across all auth modules.
  </action>
  <verify>TypeScript compiles without errors</verify>
  <done>lib/auth/types.ts exists with all required types</done>
</task>

<task type="auto">
  <name>Create password hashing utilities</name>
  <files>lib/auth/password.ts</files>
  <action>
    Implement bcrypt-based password utilities:
    - hashPassword(password: string): Promise<string> - uses bcrypt.hash with cost factor 12
    - verifyPassword(password: string, hash: string): Promise<boolean> - uses bcrypt.compare
    - validatePasswordStrength(password: string): { valid: boolean; message?: string } - min 8 chars
    
    AVOID: Storing plain text passwords
    AVOID: Using crypto.createHash - not salted, vulnerable to rainbow tables
  </action>
  <verify>Unit test: hashPassword + verifyPassword roundtrip works</verify>
  <done>lib/auth/password.ts exports hashPassword, verifyPassword, validatePasswordStrength</done>
</task>

<task type="auto">
  <name>Create JWT token utilities</name>
  <files>lib/auth/jwt.ts</files>
  <action>
    Implement JWT utilities using jose library:
    - createToken(payload: SessionPayload, secret: string): Promise<string> - Sign JWT with HS256, 24hr expiry
    - verifyToken(token: string, secret: string): Promise<SessionPayload | null> - Verify and decode
    - extractTokenFromCookie(cookies: string): string | null - Parse cookie header
    
    AVOID: jsonwebtoken library (CommonJS issues in Edge)
    AVOID: Long-lived tokens without refresh mechanism
  </action>
  <verify>TypeScript compiles; createToken/verifyToken roundtrip works</verify>
  <done>lib/auth/jwt.ts exports createToken, verifyToken, extractTokenFromCookie</done>
</task>

<task type="auto">
  <name>Create session cookie utilities</name>
  <files>lib/auth/session.ts</files>
  <action>
    Implement session management with iron-session:
    - getSession(): Promise<SessionPayload | null> - Read and verify session from cookie
    - setSession(payload: SessionPayload): Promise<void> - Create session cookie
    - clearSession(): Promise<void> - Clear session cookie
    - Session config: password from AUTH_SECRET, cookieName: 'workpulse_session', ttl: 24*60*60, secure: production
    
    AVOID: Manual cookie parsing - use iron-session for security
    AVOID: Storing sensitive data in client-accessible cookies
  </action>
  <verify>TypeScript compiles; session utilities work with iron-session</verify>
  <done>lib/auth/session.ts exports getSession, setSession, clearSession</done>
</task>

<task type="auto">
  <name>Update Supabase server client to remove auth helpers</name>
  <files>lib/supabase/server.ts</files>
  <action>
    Modify createClient() to only create a database client (no auth):
    - Remove createServerClient from @supabase/ssr
    - Use @supabase/supabase-js directly with service role key for admin operations
    - Keep anon key for public operations
    - No cookie handling for auth
    
    AVOID: Using Supabase Auth methods (signInWithPassword, signUp, getUser, etc.)
  </action>
  <verify>TypeScript compiles; createClient returns Supabase client for DB only</verify>
  <done>lib/supabase/server.ts no longer imports @supabase/ssr or handles auth cookies</done>
</task>

<task type="auto">
  <name>Update Supabase browser client to remove auth helpers</name>
  <files>lib/supabase/client.ts</files>
  <action>
    Modify createClient() to only create a database client:
    - Remove createBrowserClient from @supabase/ssr
    - Use @supabase/supabase-js directly with anon key
    - No auth cookie handling
    
    AVOID: Using Supabase Auth methods
  </action>
  <verify>TypeScript compiles; createClient returns Supabase client for DB only</verify>
  <done>lib/supabase/client.ts no longer imports @supabase/ssr or handles auth</done>
</task>

<task type="auto">
  <name>Update .env.example with new auth variables</name>
  <files>.env.example</files>
  <action>
    Replace Supabase Auth redirect URLs with:
    - AUTH_SECRET: 32+ character random string for JWT/session signing
    - DATABASE_URL: PostgreSQL connection string (or keep Supabase URL for DB)
    - Remove: NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL, SUPABASE_JWT_SECRET, etc.
    
    Keep: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY (for DB access)
  </action>
  <verify>.env.example has AUTH_SECRET and no Supabase Auth redirect vars</verify>
  <done>.env.example updated with new auth configuration</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] npm install completes without errors
- [ ] No @supabase/ssr in package.json
- [ ] lib/auth/types.ts, password.ts, jwt.ts, session.ts exist
- [ ] TypeScript compiles without errors (npx tsc --noEmit)
- [ ] .env.example has AUTH_SECRET
</verification>

<success_criteria>
- [ ] All tasks verified
- [ ] Must-haves confirmed
</success_criteria>
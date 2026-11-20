# WorkPulse Admin Dashboard Empty State Fix

## Root Cause Analysis

The admin dashboard was showing empty states (0 active team members, "—" average performance, 0 open review cycles, 0 reviews to complete, empty cards) because:

### 1. **Missing `users` Table Row for Admin User (Primary Cause)**
- All RLS policies in Supabase require a row in the `users` table with `role = 'admin'` for the authenticated user's UUID
- The policies check: `EXISTS(SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')`
- Without this row, ALL queries return empty results due to RLS filtering

### 2. **Demo Data Only in `demo_employees` Table**
- Sample data was only in the `demo_employees` table, not migrated to the main `employees` table
- The dashboard queries the `employees` table, which was empty

### 3. **No Review Cycles or Assessments Created**
- No `performance_periods` (review cycles) existed
- No `assessments` or `performance_records` existed

---

## Files Modified/Created

### 1. Database Schema (`sql/supabase_schema.sql`)
- **Added auto-create user trigger**: Creates a row in `users` table when a new Supabase Auth user signs up
- **Admin auto-promotion**: `admin@workpulse.local` automatically gets `role = 'admin'`
- **RLS policies**: Already correctly configured to check `users` table for admin/hr roles

### 2. Auth Callback (`app/auth/callback/route.ts`)
- **Added `ensureUserInUsersTable()`**: Ensures user exists in `users` table after successful authentication
- **Admin email check**: Forces `admin@workpulse.local` to have `role = 'admin'`

### 3. Dashboard Data Fetching (`components/workspace-view.tsx`)
- **Fixed table names**: Uses correct Supabase table names (`employees`, `performance_periods`, `assessments`)
- **Added fallback**: Tries `workpulse_employees` if `employees` fails
- **Role-aware**: Passes `isAdmin` to Dashboard component
- **Load Sample Data button**: Appears for admins when workspace is empty

### 4. Workspace User Context (`components/workspace-user.tsx`)
- **Extended context**: Now provides both `userId` and `role`
- **New hook**: `useWorkspaceRole()` for role-based UI

### 5. Admin Seed API (`app/api/admin/seed/route.ts`)
- **POST endpoint**: `/api/admin/seed` - seeds all sample data
- **Admin-only**: Verifies user has `role = 'admin'` via RLS
- **Idempotent**: Safe to run multiple times

### 6. Seed Script (`scripts/restore_dashboard_data.sql`)
- **Complete SQL script**: Run in Supabase SQL Editor
- **Idempotent**: Uses `ON CONFLICT DO NOTHING` / `DO UPDATE`
- **Creates**: Performance areas, app settings, demo employees, employees, review cycles, assessments, performance records, notifications
- **Verification**: Runs `get_dashboard_summary()` to confirm data

---

## How to Fix the Dashboard

### Option 1: Run the SQL Seed Script (Recommended)
1. Go to **Supabase Dashboard > SQL Editor**
2. Copy and paste the contents of `scripts/restore_dashboard_data.sql`
3. Click **Run**
4. Verify the output shows "Restore complete!" and dashboard summary with data

### Option 2: Use the "Load Sample Data" Button (After Login)
1. Log in as `admin@workpulse.local`
2. Go to `/dashboard`
3. If empty, click **"Load Sample Data"** button
4. Page will reload with sample data

### Option 3: Manual User Table Fix (If Auto-trigger Didn't Work)
1. Go to **Supabase Dashboard > Authentication > Users**
2. Find `admin@workpulse.local` and copy the **UUID**
3. Run in SQL Editor:
```sql
INSERT INTO users (id, role, full_name) 
VALUES ('PASTE-UUID-HERE', 'admin', 'Admin')
ON CONFLICT (id) DO UPDATE SET role = 'admin', full_name = 'Admin', updated_at = NOW();
```

---

## Required Supabase Dashboard Configuration

### 1. Authentication > URL Configuration
Add these **Redirect URLs**:
- `http://localhost:3000/auth/callback` (local development)
- `https://v0.app/chat/api/supabase/redirect/nT2wVXJRJLO` (v0.app)
- `https://your-app.vercel.app/auth/callback` (Vercel production)

Set **Site URL** to your deployment URL.

### 2. Database
Run the migration in `sql/supabase_schema.sql` to create tables, RLS policies, and the auto-user trigger.

---

## Verification Steps

After fixing, the dashboard should show:
- ✅ **Active team members**: 10 (from demo employees)
- ✅ **Average performance**: ~80 (from assessments)
- ✅ **Open review cycles**: 1 (Q4 2024 Review - Active)
- ✅ **Reviews to complete**: 0 (all assessments completed for active cycle)
- ✅ **Review cycles card**: Shows Q4 2024 Review as Active
- ✅ **Latest feedback card**: Shows 4 recent assessments

---

## Key Tables for Dashboard Data

| Table | Purpose | RLS Policy |
|-------|---------|------------|
| `users` | Links Supabase Auth to roles | Admin sees all |
| `employees` | Main employee directory | Admin/HR full, Employee self |
| `performance_records` | Historical metrics per employee | Admin/HR full, Employee self |
| `performance_periods` | Review cycles | Admin/HR full |
| `assessments` | Completed reviews | Admin/HR full, Employee self |
| `notifications` | Admin notifications | Admin/HR full |

---

## Troubleshooting

### Dashboard Still Empty After Seed?
1. **Check RLS**: Run `SELECT * FROM users WHERE id = auth.uid();` in SQL Editor - should return admin row
2. **Check Auth**: Ensure logged in as `admin@workpulse.local`
3. **Check Cookies**: Clear browser cookies and re-login
4. **Check Network**: Open DevTools > Network, check `/api/admin/seed` response

### "Workspace couldn't load" Error?
- Verify `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `.env.local`
- Check Supabase project is not paused
- Check RLS policies are enabled on all tables

### Seed Button Not Visible?
- Only appears for users with `role = 'admin'` in `users` table
- Only appears when `employees.length === 0 && cycles.length === 0 && assessments.length === 0`

---

## Future Prevention

1. **Auto-user trigger**: New users automatically get `users` table row on signup
2. **Admin email hardcoded**: `admin@workpulse.local` always gets admin role
3. **Seed API**: Admins can restore sample data anytime via UI
4. **Idempotent scripts**: Safe to re-run without duplicates
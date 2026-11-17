# SPEC.md — WorkPulse Vercel Migration

> **Status**: `FINALIZED`

## Vision
Replace WorkPulse's Streamlit-only runtime with a Vercel-compatible Next.js application while keeping the product's employee performance review workflow, visual identity, and secure persistent data model.

## Goals
1. **Deploy on Vercel** — Make the repository root build and run as a Next.js App Router project instead of having Vercel interpret `app.py` as a Python Function.
2. **Secure workspaces** — Use Supabase Auth (email/password) and RLS. Employees, cycles, and assessments are durable and isolated to the signed-in owner.
3. **Deliver core workflows** — Provide a polished dashboard, employee directory and CRUD, review cycle CRUD, assessment entry/history, and responsive navigation.
4. **Honest empty states** — Read all business data from Supabase; do not ship mock/sample values as though they were live records.

## Non-Goals
- Port every legacy Streamlit module (ML model evaluation, advanced analytics, exports, notification feed, settings, and admin/user management) in this migration slice.
- Retain SQLite as deployed storage; it is only part of the legacy/local Streamlit app.
- Multi-user organization membership, role administration, or cross-user sharing in this initial version.
- Expose service-role credentials or bypass RLS for normal app operations.

## Constraints
- Framework: Next.js App Router, TypeScript, Vercel-compatible root project.
- Auth/data: existing connected Supabase integration; use Supabase Auth and owner-scoped RLS tables.
- Preserve the legacy Python modules unless changing references is necessary; `app.py` may remain as the Streamlit local entry point only if Vercel is configured so it does not discover it as a Function.
- No fabricated data in the production UI.

## Success Criteria
- [ ] Vercel root build succeeds without `PYTHON_ENTRYPOINT_NOT_FOUND`.
- [ ] Email/password sign-up, email confirmation guidance, and sign-in use Supabase Auth; protected pages require an authenticated session.
- [ ] Employee and review cycle create/read/update/delete flows persist through RLS-protected Supabase tables.
- [ ] Assessments can be created and viewed, with score range and linked employee/cycle constraints enforced.
- [ ] Dashboard metrics reflect actual signed-in user's records and empty data is clearly represented.
- [ ] Desktop and mobile layouts are usable; main routes are verified in browser.
- [ ] README describes the Vercel setup and retains an accurate legacy Streamlit run path.

## Last updated
2026-11-17

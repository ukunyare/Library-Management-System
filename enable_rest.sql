-- ============================================================
--  Enable REST write access for the app (anon key)
--  Run this in: Supabase Dashboard -> SQL Editor -> New query -> Run
-- ============================================================
alter table public.admins       disable row level security;
alter table public.books        disable row level security;
alter table public.members      disable row level security;
alter table public.transactions disable row level security;
-- Done. (4 lines - your app can now write to these tables.)
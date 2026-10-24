-- Fresh application table. Apply through Supabase SQL editor after review.
-- Operator-only writes; no end-user Auth account is required.
create table if not exists public.mw_nv_matches (
 id text primary key,
 started_at timestamptz not null default now(),
 winner smallint check (winner in (0,1)),
 scores jsonb not null,
 policy_version text not null,
 replay_uri text not null,
 sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
 published boolean not null default false
);
alter table public.mw_nv_matches enable row level security;
revoke all on public.mw_nv_matches from anon, authenticated;
grant select on public.mw_nv_matches to anon, authenticated;
grant all on public.mw_nv_matches to service_role;
drop policy if exists mw_nv_published_matches on public.mw_nv_matches;
create policy mw_nv_published_matches on public.mw_nv_matches for select to anon, authenticated using (published);
-- No insert/update/delete policies for end users. service_role is server-only.

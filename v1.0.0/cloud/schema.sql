-- Apply through the Supabase SQL editor after review. No secrets in this schema.
create table if not exists public.matches (
 id text primary key,
 owner_id uuid not null references auth.users(id),
 started_at timestamptz not null default now(),
 winner smallint check (winner in (0,1)),
 scores jsonb not null,
 policy_version text not null,
 replay_uri text not null,
 sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
 published boolean not null default false
);
alter table public.matches enable row level security;
revoke all on public.matches from anon, authenticated;
grant select on public.matches to anon;
grant select, insert, update, delete on public.matches to authenticated;
create policy published_matches on public.matches for select to anon using (published);
create policy owner_read on public.matches for select to authenticated using (published or owner_id=auth.uid());
create policy owner_insert on public.matches for insert to authenticated with check (owner_id=auth.uid());
create policy owner_update on public.matches for update to authenticated using (owner_id=auth.uid()) with check (owner_id=auth.uid());
create policy owner_delete on public.matches for delete to authenticated using (owner_id=auth.uid());

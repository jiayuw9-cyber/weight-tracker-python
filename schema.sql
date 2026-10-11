-- Run in Supabase SQL Editor once. Tables are private by default.
create table if not exists public.journal_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  height_cm double precision not null default 165 check (height_cm between 100 and 220),
  start_weight double precision not null default 160 check (start_weight between 50 and 500),
  goal_weight double precision not null default 150 check (goal_weight between 50 and 500)
);

create table if not exists public.journal_progress (
  user_id uuid not null references auth.users(id) on delete cascade,
  day date not null,
  goal_lb double precision not null check (goal_lb between 50 and 500),
  actual_lb double precision check (actual_lb between 50 and 500),
  checked boolean not null default false,
  note text not null default '' check (char_length(note) <= 500),
  primary key (user_id, day)
);

alter table public.journal_settings enable row level security;
alter table public.journal_progress enable row level security;

revoke all on public.journal_settings from anon;
revoke all on public.journal_progress from anon;
grant select, insert, update, delete on public.journal_settings to authenticated;
grant select, insert, update, delete on public.journal_progress to authenticated;

create policy "settings read mine" on public.journal_settings for select to authenticated
  using ((select auth.uid()) = user_id);
create policy "settings insert mine" on public.journal_settings for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy "settings update mine" on public.journal_settings for update to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "settings delete mine" on public.journal_settings for delete to authenticated
  using ((select auth.uid()) = user_id);

create policy "progress read mine" on public.journal_progress for select to authenticated
  using ((select auth.uid()) = user_id);
create policy "progress insert mine" on public.journal_progress for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy "progress update mine" on public.journal_progress for update to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "progress delete mine" on public.journal_progress for delete to authenticated
  using ((select auth.uid()) = user_id);

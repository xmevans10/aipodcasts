-- Private account state only. Public content continues to live in Cloudflare R2.
begin;

create table public.listener_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '' check (char_length(display_name) <= 40),
  bio text not null default '' check (char_length(bio) <= 160),
  avatar_symbol text not null default 'person.fill' check (char_length(avatar_symbol) <= 80),
  avatar_hue double precision not null default 0 check (avatar_hue between 0 and 1),
  favorite_show_id text check (char_length(favorite_show_id) between 1 and 120),
  daily_goal_minutes integer not null default 10 check (daily_goal_minutes between 1 and 1440)
);

create table public.listener_show_follows (
  user_id uuid not null references auth.users(id) on delete cascade,
  show_id text not null check (char_length(show_id) between 1 and 120),
  primary key (user_id, show_id)
);

create table public.listener_episode_state (
  user_id uuid not null references auth.users(id) on delete cascade,
  episode_id text not null check (char_length(episode_id) between 1 and 200),
  saved boolean not null default false,
  listened boolean not null default false,
  position_seconds numeric(12,3) not null default 0 check (position_seconds >= 0),
  primary key (user_id, episode_id)
);

-- Never grant anonymous clients private reads or writes. No public profile directory.
alter table public.listener_profiles enable row level security;
alter table public.listener_show_follows enable row level security;
alter table public.listener_episode_state enable row level security;
revoke all on public.listener_profiles, public.listener_show_follows,
  public.listener_episode_state from public, anon, authenticated;
grant select, insert, update, delete on public.listener_profiles,
  public.listener_show_follows, public.listener_episode_state to authenticated;

create policy own_profile on public.listener_profiles for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy own_follows on public.listener_show_follows for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy own_episode_state on public.listener_episode_state for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

commit;
